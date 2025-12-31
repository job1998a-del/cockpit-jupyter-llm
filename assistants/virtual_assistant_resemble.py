import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
from dataclasses import dataclass, asdict

from api.resemble_api import ResembleAIClient
from assistant.memory_manager import MemoryManager
from assistant.emotion_engine import EmotionEngine

@dataclass
class VoiceSettings:
    voice_uuid: str
    emotion: str = "neutral"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    style: str = "conversational"

@dataclass
class ConversationState:
    user_id: str
    session_id: str
    emotional_state: Dict
    voice_settings: VoiceSettings
    conversation_history: List[Dict]
    user_preferences: Dict

class EnhancedVirtualAssistant:
    """Virtual Assistant with Resemble.AI voice synthesis and enhanced capabilities"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        self.logger.info("🚀 Initializing Enhanced Virtual Assistant...")
        
        # Resemble.AI client
        resemble_config = self.config['resemble_ai']
        self.resemble = ResembleAIClient(
            api_key=resemble_config['api_key'],
            cluster_url=resemble_config.get('cluster_url', 'https://f.cluster.resemble.ai')
        )
        
        # Memory system
        self.memory = MemoryManager(
            db_path=self.config['memory']['db_path']
        )
        
        # Emotional intelligence
        self.emotion_engine = EmotionEngine()
        
        # Voice settings
        self.default_voice = VoiceSettings(
            voice_uuid=resemble_config.get('default_voice'),
            emotion="neutral",
            speed=1.0
        )
        
        # Conversation states
        self.conversation_states: Dict[str, ConversationState] = {}
        
        # Audio cache for performance
        self.audio_cache = {}
        
        # LLM placeholder
        self.llm = None
        
        self.logger.info("✅ Enhanced Virtual Assistant initialized!")
    
    def _load_config(self, config_path: str) -> Dict:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    async def initialize(self):
        await self.resemble.initialize()
        self.logger.info("Resemble.AI client initialized")
    
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
                user_preferences=user_prefs
            )
        return self.conversation_states[key]
    
    async def process_conversation(self, 
                                  user_id: str,
                                  session_id: str,
                                  user_input: str) -> Dict:
        """Process user input and generate response"""
        state = self._get_conversation_state(user_id, session_id)
        
        # 🧠 Integration: Read system context if available
        system_context = ""
        mem_path = self.config['memory']['db_path'] + "/system_memory.json"
        if os.path.exists(mem_path):
            try:
                with open(mem_path, "r") as f:
                    sm = json.load(f)
                    if sm.get("events"):
                        latest = sm["events"][-1]
                        system_context = f"\n[System Status: {latest.get('cpu')}, Disk: {latest.get('disk')}]"
            except:
                pass

        # Simple placeholder response with system awareness
        text_response = f"I heard you say: {user_input}.{system_context} How can I help further?"
        
        # Update emotional state
        self.emotion_engine.update_state(state.emotional_state, user_input, text_response)
        
        # Adjust voice settings based on emotion
        self._adjust_voice_for_emotion(state)
        
        # Generate speech
        audio_response = await self._generate_speech(text_response, state.voice_settings)
        
        return {
            "text_response": text_response,
            "audio_response": audio_response,
            "emotional_state": state.emotional_state,
            "voice_settings": asdict(state.voice_settings)
        }
    
    def _adjust_voice_for_emotion(self, state: ConversationState):
        emotion = state.emotional_state.get('tone', 'neutral')
        mapping = {
            'happy': {'emotion': 'happy', 'speed': 1.2},
            'angry': {'emotion': 'angry', 'speed': 1.3},
            'neutral': {'emotion': 'neutral', 'speed': 1.0}
        }
        if emotion in mapping:
            state.voice_settings.emotion = mapping[emotion]['emotion']
            state.voice_settings.speed = mapping[emotion]['speed']
    
    async def _generate_speech(self, text: str, voice_settings: VoiceSettings) -> bytes:
        result = await self.resemble.synthesize(
            text=text,
            voice_uuid=voice_settings.voice_uuid,
            emotion=voice_settings.emotion,
            speed=voice_settings.speed
        )
        return result['audio'] if result['success'] else b""
    
    async def close(self):
        await self.resemble.close()
