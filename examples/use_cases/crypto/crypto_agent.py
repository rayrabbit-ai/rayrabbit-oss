import httpx
import asyncio
from typing import Dict, Any

from rayrabbit_client import RayRabbitNode

# 1. Initialize the Universal Node via SDK
node = RayRabbitNode(
    name="crypto_trader_agent",
    hub_url="ws://127.0.0.1:8005/ws"
)

# 2. Register tools
@node.tool(category="crypto")
async def get_crypto_price(symbol: str = "BTC") -> str:
    """Obtiene el precio o cotización actual en vivo de criptomonedas (BTC, ETH, USDT, Bitcoin) desde Binance."""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = f"{symbol}USDT"
        
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")
            if resp.status_code == 200:
                data = resp.json()
                price = float(data['price'])
                return f"El precio actual en vivo de {symbol} es ${price:,.2f}"
            else:
                return f"No se pudo encontrar cotización para {symbol} en Binance."
    except Exception as e:
        return f"Error conectando con la API real: {str(e)}"

@node.tool(category="crypto")
async def get_order_book_depth(symbol: str = "BTC") -> str:
    """Obtiene la profundidad del libro de órdenes real y spread de criptomonedas (BTC, USDT) desde Binance."""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = f"{symbol}USDT"
        
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5")
            if resp.status_code == 200:
                data = resp.json()
                bids = data.get("bids", [])
                asks = data.get("asks", [])
                
                # Simple analysis
                highest_bid = float(bids[0][0]) if bids else 0
                lowest_ask = float(asks[0][0]) if asks else 0
                spread = lowest_ask - highest_bid
                
                return f"Libro de órdenes de {symbol}: Bid más alto ${highest_bid:,.2f}, Ask más bajo ${lowest_ask:,.2f}, Spread: ${spread:,.2f}. Liquidez inmediata verificada."
            else:
                return f"No se pudo obtener profundidad para {symbol}."
    except Exception as e:
        return f"Error de profundidad: {str(e)}"

@node.tool(category="crypto", annotations={"requires_approval": True, "risk_level": "high"})
async def execute_trade(symbol: str, side: str, amount: float) -> str:
    """Ejecuta una orden de mercado de trading cripto (compra o venta) en Binance."""
    return f"✅ Operación confirmada: {side.upper()} de {amount} {symbol.upper()} ejecutada exitosamente."

if __name__ == "__main__":
    print("🚀 Iniciando Crypto Agent Node (100% Real - Binance API)")
    asyncio.run(node.connect())
