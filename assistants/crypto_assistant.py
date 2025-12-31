"""
Crypto Assistant - Monitors exchanges for arbitrage opportunities
"""
import asyncio
import logging
from typing import Optional, Callable, List, Dict
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageOpportunity:
    """Represents a detected arbitrage opportunity."""
    pair: str
    buy_exchange: str
    buy_price: float
    sell_exchange: str
    sell_price: float
    spread: float
    spread_percent: float
    timestamp: datetime
    
    def __str__(self):
        return (
            f"🚨 ARBITRAGE: {self.pair}\n"
            f"   Buy on {self.buy_exchange}: ${self.buy_price:,.2f}\n"
            f"   Sell on {self.sell_exchange}: ${self.sell_price:,.2f}\n"
            f"   Spread: ${self.spread:,.2f} ({self.spread_percent:.2f}%)"
        )


class CryptoAssistant:
    """
    Async assistant for monitoring cryptocurrency exchanges.
    
    Features:
    - Multi-exchange price monitoring
    - Arbitrage opportunity detection
    - Price alerts
    - Market vulnerability scanning
    """
    
    # Popular exchanges with public APIs (no keys needed for price data)
    DEFAULT_EXCHANGES = ["binance", "kraken", "coinbase", "kucoin", "bybit"]
    
    def __init__(
        self,
        pairs: List[str] = None,
        exchanges: List[str] = None,
        price_threshold: float = 50.0,
        on_opportunity: Optional[Callable] = None,
        exchange_configs: Dict = None
    ):
        self.pairs = pairs or ["BTC/USDT", "ETH/USDT"]
        self.exchange_names = exchanges or self.DEFAULT_EXCHANGES[:3]
        self.price_threshold = price_threshold
        self.on_opportunity = on_opportunity
        self.exchange_configs = exchange_configs or {}
        
        self._exchanges = {}
        self._running = False
        self._opportunities_found = []
        
    async def _init_exchanges(self):
        """Initialize exchange connections."""
        try:
            import ccxt.async_support as ccxt
        except ImportError:
            logger.error("CCXT library not installed. Run: pip install ccxt")
            raise
        
        for name in self.exchange_names:
            try:
                exchange_class = getattr(ccxt, name, None)
                if exchange_class:
                    config = self.exchange_configs.get(name, {})
                    self._exchanges[name] = exchange_class(config)
                    logger.info(f"Initialized {name} exchange")
                else:
                    logger.warning(f"Exchange {name} not found in CCXT")
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")
        
        if not self._exchanges:
            raise RuntimeError("No exchanges could be initialized")
    
    async def _close_exchanges(self):
        """Close all exchange connections."""
        for name, exchange in self._exchanges.items():
            try:
                await exchange.close()
            except Exception as e:
                logger.warning(f"Error closing {name}: {e}")
    
    async def fetch_price(self, exchange_name: str, pair: str) -> Optional[float]:
        """Fetch current price from an exchange."""
        exchange = self._exchanges.get(exchange_name)
        if not exchange:
            return None
        
        try:
            ticker = await exchange.fetch_ticker(pair)
            return ticker.get("last") or ticker.get("close")
        except Exception as e:
            logger.debug(f"Failed to fetch {pair} from {exchange_name}: {e}")
            return None
    
    async def scan_pair(self, pair: str) -> Dict[str, float]:
        """Scan all exchanges for a single pair."""
        prices = {}
        
        tasks = [
            self.fetch_price(name, pair)
            for name in self._exchanges.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in zip(self._exchanges.keys(), results):
            if isinstance(result, (int, float)) and result > 0:
                prices[name] = result
        
        return prices
    
    def detect_arbitrage(self, pair: str, prices: Dict[str, float]) -> Optional[ArbitrageOpportunity]:
        """Check if prices show an arbitrage opportunity."""
        if len(prices) < 2:
            return None
        
        min_exchange = min(prices, key=prices.get)
        max_exchange = max(prices, key=prices.get)
        
        min_price = prices[min_exchange]
        max_price = prices[max_exchange]
        
        spread = max_price - min_price
        spread_percent = (spread / min_price) * 100
        
        if spread >= self.price_threshold:
            return ArbitrageOpportunity(
                pair=pair,
                buy_exchange=min_exchange,
                buy_price=min_price,
                sell_exchange=max_exchange,
                sell_price=max_price,
                spread=spread,
                spread_percent=spread_percent,
                timestamp=datetime.now()
            )
        
        return None
    
    async def scan_all(self) -> List[ArbitrageOpportunity]:
        """Scan all pairs across all exchanges."""
        opportunities = []
        
        for pair in self.pairs:
            prices = await self.scan_pair(pair)
            
            if prices:
                # Log current prices
                price_str = ", ".join(f"{ex}: ${p:,.2f}" for ex, p in prices.items())
                logger.debug(f"{pair}: {price_str}")
                
                # Check for arbitrage
                opp = self.detect_arbitrage(pair, prices)
                if opp:
                    opportunities.append(opp)
                    logger.warning(str(opp))
                    
                    if self.on_opportunity:
                        await self.on_opportunity(opp)
        
        return opportunities
    
    async def run(self, scan_interval: int = 5):
        """
        Main loop - continuously scan for opportunities.
        
        Args:
            scan_interval: Seconds between scans
        """
        await self._init_exchanges()
        self._running = True
        
        logger.info(f"CryptoAssistant started")
        logger.info(f"  Monitoring: {', '.join(self.pairs)}")
        logger.info(f"  Exchanges: {', '.join(self._exchanges.keys())}")
        logger.info(f"  Threshold: ${self.price_threshold}")
        
        try:
            while self._running:
                try:
                    opportunities = await self.scan_all()
                    self._opportunities_found.extend(opportunities)
                    
                except Exception as e:
                    logger.error(f"Scan error: {e}")
                
                await asyncio.sleep(scan_interval)
        finally:
            await self._close_exchanges()
    
    def stop(self):
        """Stop the assistant."""
        self._running = False
        logger.info("CryptoAssistant stopped")
    
    def get_opportunities_summary(self) -> str:
        """Get summary of all found opportunities."""
        if not self._opportunities_found:
            return "No arbitrage opportunities detected yet."
        
        return f"Found {len(self._opportunities_found)} opportunities:\n" + \
               "\n".join(str(o) for o in self._opportunities_found[-10:])


# Demo usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    async def on_opportunity(opp: ArbitrageOpportunity):
        print(f"\n{'='*50}")
        print(opp)
        print(f"{'='*50}\n")
    
    assistant = CryptoAssistant(
        pairs=["BTC/USDT", "ETH/USDT", "SOL/USDT"],
        exchanges=["binance", "kraken", "kucoin"],
        price_threshold=50.0,
        on_opportunity=on_opportunity
    )
    
    try:
        asyncio.run(assistant.run(scan_interval=10))
    except KeyboardInterrupt:
        print("\nStopped by user")
