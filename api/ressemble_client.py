# ressemble_client.py
import requests
import json
import os

class ResembleClient:
    def __init__(self, api_key: str, synth_url=None, stream_url=None):
        self.api_key = api_key
        self.synth_url = synth_url or "https://f.cluster.resemble.ai/synthesize"
        self.stream_url = stream_url or "https://f.cluster.resemble.ai/stream"
        self.headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json"
        }

    def synthesize(self, text: str, voice: str, output_file="output.wav"):
        payload = {
            "voice": voice,
            "input_text": text,
            "format": "wav"
        }

        try:
            response = requests.post(self.synth_url, 
                                     headers=self.headers, 
                                     data=json.dumps(payload))
            response.raise_for_status()
        except Exception as e:
            return {"error": str(e), "status_code": getattr(e, "response", None)}

        # Save audio file
        with open(output_file, "wb") as f:
            f.write(response.content)

        return {"status": "ok", "file": output_file}

    def stream_synthesis(self, text: str, voice: str):
        """
        Streaming endpoint — useful for real-time voice feedback.
        It yields audio chunks.
        """
        payload = {
            "voice": voice,
            "input_text": text
        }

        with requests.post(self.stream_url,
                           headers=self.headers,
                           json=payload,
                           stream=True) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
