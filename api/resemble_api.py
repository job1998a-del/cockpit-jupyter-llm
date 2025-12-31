import requests
import json
import base64
from typing import Dict, List, Optional
import asyncio
import aiohttp
from dataclasses import dataclass
import logging

@dataclass
class VoiceProfile:
    uuid: str
    name: str
    language: str
    gender: str
    age_group: str
    style: str

@dataclass
class Project:
    uuid: str
    name: str
    description: str
    default_voice: str

class ResembleAIClient:
    """High-performance Resemble.AI API client with streaming support"""
    
    def __init__(self, api_key: str, cluster_url: str = "https://f.cluster.resemble.ai"):
        self.api_key = api_key
        self.base_url = cluster_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Cache for voices and projects
        self.voices: Dict[str, VoiceProfile] = {}
        self.projects: Dict[str, Project] = {}
        
        # Session for async requests
        self.session = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize async session and cache data"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        await self._cache_voices()
        await self._cache_projects()
    
    async def _cache_voices(self):
        """Cache available voices"""
        try:
            url = f"{self.base_url}/api/v1/voices"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    for voice in data.get('items', []):
                        voice_profile = VoiceProfile(
                            uuid=voice.get('uuid'),
                            name=voice.get('name'),
                            language=voice.get('language'),
                            gender=voice.get('gender'),
                            age_group=voice.get('age_group'),
                            style=voice.get('style', 'neutral')
                        )
                        self.voices[voice_profile.uuid] = voice_profile
                    
                    self.logger.info(f"Cached {len(self.voices)} voices")
                else:
                    self.logger.error(f"Failed to fetch voices: {response.status}")
        except Exception as e:
            self.logger.error(f"Error caching voices: {e}")
    
    async def _cache_projects(self):
        """Cache available projects"""
        try:
            url = f"{self.base_url}/api/v1/projects"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    for project in data.get('items', []):
                        project_obj = Project(
                            uuid=project.get('uuid'),
                            name=project.get('name'),
                            description=project.get('description'),
                            default_voice=project.get('default_voice')
                        )
                        self.projects[project_obj.uuid] = project_obj
                    
                    self.logger.info(f"Cached {len(self.projects)} projects")
                else:
                    self.logger.error(f"Failed to fetch projects: {response.status}")
        except Exception as e:
            self.logger.error(f"Error caching projects: {e}")
    
    async def synthesize(self, 
                        text: str, 
                        voice_uuid: str,
                        project_uuid: Optional[str] = None,
                        format: str = "mp3",
                        sample_rate: int = 22050,
                        precision: str = "PCM_16",
                        include_timestamps: bool = False,
                        emotion: Optional[str] = None,
                        speed: float = 1.0) -> Dict:
        """
        Synthesize speech using Resemble.AI
        """
        
        payload = {
            "text": text,
            "voice_uuid": voice_uuid,
            "format": format,
            "sample_rate": sample_rate,
            "precision": precision,
            "include_timestamps": include_timestamps,
            "output_type": "audio"
        }
        
        if project_uuid:
            payload["project_uuid"] = project_uuid
        
        if emotion:
            payload["emotion"] = emotion
        
        if speed != 1.0:
            payload["speed"] = speed
        
        try:
            url = f"{self.base_url}/api/v1/projects/{project_uuid}/clips" if project_uuid else f"{self.base_url}/api/v1/synthesize"
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('audio'):
                        audio_data = base64.b64decode(data['audio'])
                        
                        return {
                            "success": True,
                            "audio": audio_data,
                            "format": format,
                            "sample_rate": sample_rate,
                            "timestamps": data.get('timestamps', []),
                            "voice_uuid": voice_uuid,
                            "duration": data.get('duration', 0),
                            "id": data.get('id')
                        }
                    else:
                        return {"success": False, "error": "No audio data in response"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"API request failed: {response.status}", "details": error_text}
        
        except Exception as e:
            self.logger.error(f"Synthesis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def stream_synthesis(self, 
                              text: str,
                              voice_uuid: str,
                              project_uuid: Optional[str] = None,
                              chunk_size: int = 2048,
                              callback=None) -> bytes:
        """Stream synthesis for real-time applications"""
        
        payload = {
            "text": text,
            "voice_uuid": voice_uuid,
            "stream": True,
            "format": "wav",
            "sample_rate": 16000
        }
        
        if project_uuid:
            payload["project_uuid"] = project_uuid
        
        try:
            url = f"{self.base_url}/stream"
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_chunks = []
                    
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if callback:
                            await callback(chunk)
                        audio_chunks.append(chunk)
                    
                    return b''.join(audio_chunks)
                else:
                    error_text = await response.text()
                    self.logger.error(f"Streaming failed: {error_text}")
                    return None
        
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
            return None
    
    async def create_voice_clone(self, 
                                name: str,
                                audio_samples: List[bytes],
                                language: str = "en",
                                gender: str = "unspecified",
                                age_group: str = "adult") -> Optional[str]:
        """Create a custom voice clone"""
        
        encoded_samples = []
        for i, audio in enumerate(audio_samples[:50]):
            encoded_samples.append({
                "audio": base64.b64encode(audio).decode('utf-8'),
                "filename": f"sample_{i}.wav"
            })
        
        payload = {
            "name": name,
            "language": language,
            "gender": gender,
            "age_group": age_group,
            "samples": encoded_samples
        }
        
        try:
            url = f"{self.base_url}/api/v1/voices"
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 201:
                    data = await response.json()
                    voice_uuid = data.get('uuid')
                    
                    if voice_uuid:
                        self.voices[voice_uuid] = VoiceProfile(
                            uuid=voice_uuid,
                            name=name,
                            language=language,
                            gender=gender,
                            age_group=age_group,
                            style="custom"
                        )
                    return voice_uuid
                else:
                    return None
        except Exception as e:
            self.logger.error(f"Voice creation error: {e}")
            return None
            
    async def close(self):
        if self.session:
            await self.session.close()
