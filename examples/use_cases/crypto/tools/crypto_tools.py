"""
Herramientas Agnósticas para el Caso de Uso Crypto.
Provee funciones puras de Python para conectarse a la API pública de Binance.
No contiene decoradores de frameworks específicos (LangChain, CrewAI, AutoGen).
"""
import httpx
from typing import Dict, Any

def get_crypto_price(symbol: str) -> str:
    """Obtiene la cotización actual de una criptomoneda desde la API pública de Binance."""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = f"{symbol}USDT"
    
    try:
        response = httpx.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        price = float(data.get("price", 0.0))
        return f"El precio actual de {symbol} es ${price:,.2f}"
    except httpx.HTTPStatusError as e:
        return f"Error al consultar el precio: El par {symbol} no existe o la API rechazó la consulta ({e.response.status_code})."
    except Exception as e:
        return f"Error de red al consultar Binance: {str(e)}"

def get_order_book_depth(symbol: str) -> str:
    """Obtiene la profundidad del libro de órdenes (Bid/Ask) desde la API pública de Binance."""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = f"{symbol}USDT"
    
    try:
        response = httpx.get(f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        
        if not bids or not asks:
            return f"Libro de órdenes vacío para {symbol}."
            
        highest_bid = float(bids[0][0])
        lowest_ask = float(asks[0][0])
        spread = lowest_ask - highest_bid
        
        return (f"Profundidad de mercado para {symbol}:\n"
                f"- Mejor precio de compra (Bid): ${highest_bid:,.2f}\n"
                f"- Mejor precio de venta (Ask): ${lowest_ask:,.2f}\n"
                f"- Spread: ${spread:,.2f}")
    except Exception as e:
        return f"Error al consultar el libro de órdenes: {str(e)}"

def analyze_sentiment(symbol: str) -> str:
    """Analiza el sentimiento de mercado basado en la volatilidad de las últimas 24h en Binance."""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = f"{symbol}USDT"
        
    try:
        response = httpx.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        
        price_change_percent = float(data.get("priceChangePercent", 0.0))
        
        if price_change_percent > 5.0:
            sentiment = "Extremadamente Alcista (Bullish)"
        elif price_change_percent > 1.0:
            sentiment = "Ligeramente Alcista"
        elif price_change_percent < -5.0:
            sentiment = "Extremadamente Bajista (Bearish)"
        elif price_change_percent < -1.0:
            sentiment = "Ligeramente Bajista"
        else:
            sentiment = "Neutral (Consolidación)"
            
        return f"El sentimiento cuantitativo 24h para {symbol} es {sentiment} (Cambio: {price_change_percent}%)."
    except Exception as e:
        return f"Error al consultar volatilidad 24h: {str(e)}"

# Exportar explícitamente las funciones que se pueden convertir en tools
__all__ = ["get_crypto_price", "get_order_book_depth", "analyze_sentiment"]
