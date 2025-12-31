from langchain.tools import Tool
from langchain.agents import tool
import subprocess
import requests
from bs4 import BeautifulSoup
from readability import Document
from typing import List, Optional
import json
import logging

logger = logging.getLogger(__name__)

@tool
def shell_command(cmd: str) -> str:
    """Execute a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        return f"Exit Code: {result.returncode}\nOutput: {result.stdout}\nError: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def web_search(query: str) -> str:
    """Search the web and return summarized results."""
    try:
        # DuckDuckGo HTML search
        url = "https://html.duckduckgo.com/html/"
        params = {"q": query, "kl": "us-en"}
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; CockpitAI/1.0)"
        }
        
        response = requests.post(url, data=params, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        results = []
        for result in soup.find_all("a", class_="result__url", limit=3):
            link = result.get("href")
            if link and link.startswith("http"):
                try:
                    page_resp = requests.get(link, timeout=10, headers=headers)
                    doc = Document(page_resp.text)
                    summary = BeautifulSoup(doc.summary(), "html.parser").get_text()[:500]
                    results.append(f"Source: {link}\nSummary: {summary}")
                except:
                    continue
        
        return "\n\n".join(results) if results else "No results found"
    except Exception as e:
        return f"Search error: {str(e)}"

@tool
def crypto_prices(symbols: Optional[str] = None) -> str:
    """Get current cryptocurrency prices. Provide symbols separated by commas (e.g. BTC/USDT,ETH/USDT)."""
    try:
        import ccxt
        exchange = ccxt.binance()
        
        symbol_list = []
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(",")]
        else:
            symbol_list = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "SOL/USDT"]
        
        prices = {}
        for symbol in symbol_list:
            try:
                ticker = exchange.fetch_ticker(symbol)
                prices[symbol] = {
                    "price": ticker["last"],
                    "change": ticker["percentage"],
                    "volume": ticker["baseVolume"]
                }
            except Exception as se:
                logger.error(f"Error fetching {symbol}: {se}")
                continue
        
        return json.dumps(prices, indent=2)
    except Exception as e:
        return f"Crypto API error: {str(e)}"

def get_available_tools() -> List[Tool]:
    """Return list of available tools based on configuration."""
    tools = []
    
    # Always include these basic tools
    tools.extend([
        Tool(
            name="Shell",
            func=shell_command,
            description="Execute shell commands (use with caution)"
        ),
        Tool(
            name="WebSearch", 
            func=web_search,
            description="Search the web for current information"
        )
    ])
    
    # Optional crypto tool
    try:
        import ccxt
        tools.append(
            Tool(
                name="CryptoPrices",
                func=crypto_prices,
                description="Get cryptocurrency prices from Binance"
            )
        )
    except ImportError:
        pass
    
    return tools
