"""
Call Assistant - Handles phone calls and SMS via Twilio
"""
import asyncio
import logging
from typing import Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class CallAssistant:
    """
    Async assistant for handling phone calls and SMS via Twilio.
    
    Features:
    - Monitor incoming calls/SMS
    - Make outbound calls
    - Send SMS messages
    - Voice response handling (TwiML)
    """
    
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        phone_number: str,
        on_message: Optional[Callable] = None,
        on_call: Optional[Callable] = None
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.phone_number = phone_number
        self.on_message = on_message
        self.on_call = on_call
        self._client = None
        self._running = False
        
    def _get_client(self):
        """Lazy initialization of Twilio client."""
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized successfully")
            except ImportError:
                logger.error("Twilio library not installed. Run: pip install twilio")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                raise
        return self._client
    
    async def send_sms(self, to: str, message: str) -> dict:
        """
        Send an SMS message.
        
        Args:
            to: Recipient phone number (E.164 format, e.g., +1234567890)
            message: Message content
            
        Returns:
            Message SID and status
        """
        client = self._get_client()
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        msg = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to
            )
        )
        
        logger.info(f"SMS sent to {to}: SID={msg.sid}")
        return {"sid": msg.sid, "status": msg.status}
    
    async def make_call(self, to: str, twiml_url: str) -> dict:
        """
        Initiate an outbound call.
        
        Args:
            to: Recipient phone number
            twiml_url: URL returning TwiML for call handling
            
        Returns:
            Call SID and status
        """
        client = self._get_client()
        
        loop = asyncio.get_event_loop()
        call = await loop.run_in_executor(
            None,
            lambda: client.calls.create(
                url=twiml_url,
                from_=self.phone_number,
                to=to
            )
        )
        
        logger.info(f"Call initiated to {to}: SID={call.sid}")
        return {"sid": call.sid, "status": call.status}
    
    async def get_recent_messages(self, limit: int = 10) -> list:
        """Fetch recent incoming messages."""
        client = self._get_client()
        
        loop = asyncio.get_event_loop()
        messages = await loop.run_in_executor(
            None,
            lambda: list(client.messages.list(to=self.phone_number, limit=limit))
        )
        
        return [
            {
                "from": msg.from_,
                "body": msg.body,
                "date": str(msg.date_sent),
                "sid": msg.sid
            }
            for msg in messages
        ]
    
    async def run(self, poll_interval: int = 30):
        """
        Main loop - poll for incoming messages/calls.
        
        For production, consider using webhooks instead of polling.
        """
        self._running = True
        logger.info("CallAssistant started - monitoring for calls/messages...")
        
        seen_messages = set()
        
        while self._running:
            try:
                # Check for new messages
                messages = await self.get_recent_messages(limit=5)
                
                for msg in messages:
                    if msg["sid"] not in seen_messages:
                        seen_messages.add(msg["sid"])
                        logger.info(f"New message from {msg['from']}: {msg['body'][:50]}...")
                        
                        if self.on_message:
                            await self.on_message(msg)
                
                # Keep seen_messages from growing indefinitely
                if len(seen_messages) > 100:
                    seen_messages = set(list(seen_messages)[-50:])
                    
            except Exception as e:
                logger.error(f"Error in CallAssistant loop: {e}")
            
            await asyncio.sleep(poll_interval)
    
    def stop(self):
        """Stop the assistant."""
        self._running = False
        logger.info("CallAssistant stopped")


# Demo usage
if __name__ == "__main__":
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        assistant = CallAssistant(
            account_sid=config["twilio"]["account_sid"],
            auth_token=config["twilio"]["auth_token"],
            phone_number=config["twilio"]["phone_number"]
        )
        
        asyncio.run(assistant.run())
    else:
        print(f"Config not found at {config_path}")
        print("Copy config/config.example.yaml to config/config.yaml and add your credentials.")
