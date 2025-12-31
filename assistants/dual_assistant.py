"""
Dual Assistant - Orchestrates phone and crypto assistants concurrently
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

import yaml

from .call_assistant import CallAssistant
from .crypto_assistant import CryptoAssistant, ArbitrageOpportunity

logger = logging.getLogger(__name__)


class DualAssistant:
    """
    Orchestrates both CallAssistant and CryptoAssistant concurrently.
    
    Features:
    - Runs both assistants in parallel using asyncio
    - Optional SMS alerts for crypto opportunities
    - Graceful shutdown handling
    - Configuration from YAML file
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "config.yaml"
        self.config = {}
        self.call_assistant: Optional[CallAssistant] = None
        self.crypto_assistant: Optional[CryptoAssistant] = None
        self._tasks = []
        
    def load_config(self) -> bool:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config not found: {self.config_path}")
            logger.info("Using default settings. Copy config.example.yaml to config.yaml for full features.")
            return False
        
        try:
            with open(self.config_path) as f:
                self.config = yaml.safe_load(f) or {}
            logger.info(f"Loaded config from {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def _init_call_assistant(self) -> Optional[CallAssistant]:
        """Initialize the call assistant from config."""
        twilio_config = self.config.get("twilio", {})
        
        account_sid = twilio_config.get("account_sid", "")
        auth_token = twilio_config.get("auth_token", "")
        phone_number = twilio_config.get("phone_number", "")
        
        # Check for placeholder values
        if not account_sid or "YOUR_" in account_sid:
            logger.warning("Twilio not configured - CallAssistant disabled")
            logger.info("Add your Twilio credentials to config.yaml to enable phone features")
            return None
        
        async def on_message(msg):
            logger.info(f"📱 Received SMS from {msg['from']}: {msg['body']}")
        
        return CallAssistant(
            account_sid=account_sid,
            auth_token=auth_token,
            phone_number=phone_number,
            on_message=on_message
        )
    
    def _init_crypto_assistant(self) -> CryptoAssistant:
        """Initialize the crypto assistant from config."""
        crypto_config = self.config.get("crypto", {})
        
        pairs = crypto_config.get("pairs", ["BTC/USDT", "ETH/USDT"])
        threshold = crypto_config.get("price_threshold", 100)
        
        # Get exchange configs (for authenticated access)
        exchange_configs = {}
        for name, creds in crypto_config.get("exchanges", {}).items():
            if creds.get("api_key"):
                exchange_configs[name] = {
                    "apiKey": creds["api_key"],
                    "secret": creds["secret"]
                }
        
        async def on_opportunity(opp: ArbitrageOpportunity):
            logger.warning(f"🚨 {opp}")
            
            # Send SMS alert if call assistant is available
            if self.call_assistant:
                try:
                    await self.call_assistant.send_sms(
                        to=self.config.get("twilio", {}).get("alert_number", ""),
                        message=f"Arbitrage Alert!\n{opp.pair}: ${opp.spread:.2f} spread\n"
                                f"Buy {opp.buy_exchange} @ ${opp.buy_price:,.2f}\n"
                                f"Sell {opp.sell_exchange} @ ${opp.sell_price:,.2f}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send SMS alert: {e}")
        
        return CryptoAssistant(
            pairs=pairs,
            price_threshold=threshold,
            exchange_configs=exchange_configs,
            on_opportunity=on_opportunity
        )
    
    async def run(self):
        """Run both assistants concurrently."""
        self.load_config()
        
        # Initialize assistants
        self.call_assistant = self._init_call_assistant()
        self.crypto_assistant = self._init_crypto_assistant()
        
        # Create tasks
        tasks = []
        
        if self.call_assistant:
            poll_interval = self.config.get("twilio", {}).get("poll_interval", 30)
            tasks.append(asyncio.create_task(
                self.call_assistant.run(poll_interval=poll_interval),
                name="call_assistant"
            ))
            logger.info("✅ CallAssistant started")
        
        if self.crypto_assistant:
            scan_interval = self.config.get("crypto", {}).get("scan_interval", 5)
            tasks.append(asyncio.create_task(
                self.crypto_assistant.run(scan_interval=scan_interval),
                name="crypto_assistant"
            ))
            logger.info("✅ CryptoAssistant started")
        
        if not tasks:
            logger.error("No assistants could be started!")
            return
        
        self._tasks = tasks
        
        print("\n" + "="*60)
        print("🤖 DUAL ASSISTANT RUNNING")
        print("="*60)
        print(f"  📱 Phone/SMS: {'ENABLED' if self.call_assistant else 'DISABLED (configure Twilio)'}")
        print(f"  📊 Crypto Scanner: ENABLED")
        print(f"     Pairs: {', '.join(self.crypto_assistant.pairs)}")
        print(f"     Threshold: ${self.crypto_assistant.price_threshold}")
        print("="*60)
        print("Press Ctrl+C to stop\n")
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled")
    
    def stop(self):
        """Stop all assistants."""
        if self.call_assistant:
            self.call_assistant.stop()
        if self.crypto_assistant:
            self.crypto_assistant.stop()
        
        for task in self._tasks:
            task.cancel()


def setup_signal_handlers(assistant: DualAssistant):
    """Set up graceful shutdown on SIGINT/SIGTERM."""
    def handler(signum, frame):
        print("\n🛑 Shutting down gracefully...")
        assistant.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def main():
    """Entry point for the dual assistant."""
    # Configure logging
    log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s │ %(levelname)-8s │ %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Reduce noise from libraries
    logging.getLogger("ccxt").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Create and run assistant
    assistant = DualAssistant()
    setup_signal_handlers(assistant)
    
    try:
        asyncio.run(assistant.run())
    except KeyboardInterrupt:
        print("\nStopped by user")


if __name__ == "__main__":
    main()
