import asyncio
import json
import logging
import os
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from config.settings import settings

from api.resemble_api import ResembleAIClient
from assistant.memory_manager import MemoryManager
from assistant.emotion_engine import EmotionEngine
from assistant.goals import GoalEngine
from assistant.voice import human_pause
from assistant.tools import ToolEngine
from assistant.debate import internal_debate
from assistant.ethics import ethics_filter

@dataclass
class VoiceSettings:
    voice_uuid: str
    emotion: str = "neutral"
    speed: float = 1.0

@dataclass
class ConversationState:
    user_id: str
    session_id: str
    emotional_state: Dict
    voice_settings: VoiceSettings
    conversation_history: List[Dict]
    user_preferences: Dict
    beliefs: List[str]

class HumanLikeAgent:
    """
    "Almost Human" Ollama Agent with autonomous goals, internal debate, 
    and system awareness.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        try:
            self.config = self._load_config(config_path)
        except:
            self.config = {}
            
        self.logger = self._setup_logging()
        
        # Resemble Settings
        resemble_key = self.config.get('resemble_ai', {}).get('api_key', settings.resemble_api_key)
        resemble_url = self.config.get('resemble_ai', {}).get('cluster_url', "https://f.cluster.resemble.ai")
        default_voice_uuid = self.config.get('resemble_ai', {}).get('default_voice', settings.resemble_default_voice)

        # Initialize Core Components
        self.resemble = ResembleAIClient(
            api_key=resemble_key,
            cluster_url=resemble_url
        )
        
        db_path = self.config.get('memory', {}).get('db_path', "./memory_db")
        self.memory = MemoryManager(db_path=db_path)
        self.emotion_engine = EmotionEngine()
        self.goal_engine = GoalEngine(self.ollama_query)
        self.tool_engine = ToolEngine(self.ollama_query)
        
        self.default_voice = VoiceSettings(
            voice_uuid=default_voice_uuid,
            emotion="neutral"
        )
        
        self.conversation_states: Dict[str, ConversationState] = {}
        self.ollama_url = self.config.get('ollama', {}).get('url', settings.ollama_base_url + "/api/generate")

    def _load_config(self, config_path: str) -> Dict:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)

    async def initialize(self):
        await self.resemble.initialize()
        self.logger.info("HumanLikeAgent initialized with 'Almost Human' stack")

    async def ollama_query(self, model: str, prompt: str) -> str:
        """Call local Ollama API for generation."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.ollama_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", "")
                    else:
                        self.logger.error(f"Ollama error: {response.status}")
                        return "I'm having trouble thinking right now."
        except Exception as e:
            self.logger.error(f"Ollama connection error: {e}")
            return "Ollama is not reachable."

    def _get_conversation_state(self, user_id: str, session_id: str) -> ConversationState:
        key = f"{user_id}:{session_id}"
        if key not in self.conversation_states:
            user_prefs = self.memory.get_user_preferences(user_id)
            self.conversation_states[key] = ConversationState(
                user_id=user_id,
                session_id=session_id,
                emotional_state=self.emotion_engine.get_default_state(),
                voice_settings=self.default_voice,
                conversation_history=[],
                user_preferences=user_prefs,
                beliefs=[]
            )
        return self.conversation_states[key]

    async def process_conversation(self, user_id: str, session_id: str, user_input: str) -> Dict:
        state = self._get_conversation_state(user_id, session_id)
        
        # 1. Goal Detection
        goal = await self.goal_engine.decide_goal(user_input)
        self.logger.info(f"Target Goal: {goal}")

        # 2. Internal Thought (System Context Awareness)
        system_context = self._get_system_context()
        thought_prompt = f"System Context: {system_context}\nGoal: {goal}\nUser Input: {user_input}\nThink silently."
        thoughts = await self.ollama_query("qwen2.5:0.5b", thought_prompt)

        # 3. Internal Debate
        raw_response = await internal_debate(user_input, self.ollama_query)

        # 4. Tool Use Decision
        tool_name = await self.tool_engine.decide_tool(user_input)
        tool_result = ""
        if tool_name != "none":
            # Extracting command is more complex, but for demo we use shell input
            tool_result = f"\n[Action Result: {await self.tool_engine.execute(tool_name, user_input[:50])}]"

        # 5. Ethics Filter
        final_text = await ethics_filter(raw_response + tool_result, user_input, self.ollama_query)

        # 6. Self-Learning (Belief Consolidation)
        self._learn(state, user_input, final_text)

        # 7. Voice Realism (Pause Simulation)
        await human_pause(final_text)

        # 8. Emotional Integration & Voice Generation
        self.emotion_engine.update_state(state.emotional_state, user_input, final_text)
        self._adjust_voice_for_emotion(state)
        
        audio_response = await self._generate_speech(final_text, state.voice_settings)
        
        return {
            "text_response": final_text,
            "audio_response": audio_response,
            "emotional_state": state.emotional_state,
            "voice_settings": asdict(state.voice_settings),
            "goal": goal,
            "tool_used": tool_name
        }

    def _get_system_context(self) -> str:
        mem_path = self.config['memory']['db_path'] + "/system_memory.json"
        if os.path.exists(mem_path):
            try:
                with open(mem_path, "r") as f:
                    sm = json.load(f)
                    if sm.get("events"):
                        latest = sm["events"][-1]
                        return f"CPU: {latest.get('cpu')}, Disk: {latest.get('disk')}"
            except:
                pass
        return "Unknown"

    def _learn(self, state, user_input, response):
        """Persistent self-learning step."""
        state.beliefs.append(response[:100])
        if len(state.beliefs) > 20:
            state.beliefs.pop(0)
        self.memory.store_conversation(state.user_id, user_input, response, {"beliefs": state.beliefs})

    def _adjust_voice_for_emotion(self, state: ConversationState):
        emotion = state.emotional_state.get('tone', 'neutral')
        mapping = {'happy': {'emotion': 'happy', 'speed': 1.2}, 'angry': {'emotion': 'angry', 'speed': 1.3}, 'neutral': {'emotion': 'neutral', 'speed': 1.0}}
        if emotion in mapping:
            state.voice_settings.emotion = mapping[emotion]['emotion']
            state.voice_settings.speed = mapping[emotion]['speed']

    async def _generate_speech(self, text: str, voice_settings: VoiceSettings) -> bytes:
        result = await self.resemble.synthesize(text=text, voice_uuid=voice_settings.voice_uuid, emotion=voice_settings.emotion, speed=voice_settings.speed)
        return result['audio'] if result['success'] else b""

    async def close(self):
        await self.resemble.close()
