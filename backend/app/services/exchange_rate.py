"""
Servicio para obtener tasas de cambio históricas
Usa frankfurter.app - API gratuita sin límites basada en BCE
"""

import time
import logging
import requests
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger(__name__)

# API gratuita Banco Central Europeo
EXCHANGE_API_URL = "https://api.frankfurter.app"

# PERF-H2: Caché en memoria por worker — evita llamadas API repetidas para la misma moneda+fecha.
# Con 2 workers gunicorn, cada uno tiene su propia caché. Peor caso: 2 requests por combinación
# en vez de 1, que es aceptable vs los 10+ requests idénticos de antes.
_rate_cache: dict = {}  # {(currency, date_str): (rate, timestamp)}
_CACHE_TTL = 3600  # 1 hora


def _get_cached_rate(currency: str, date_str: str) -> Optional[float]:
    key = (currency.upper(), date_str)
    if key in _rate_cache:
        rate, ts = _rate_cache[key]
        if time.time() - ts < _CACHE_TTL:
            return rate
        del _rate_cache[key]
    return None


def _set_cached_rate(currency: str, date_str: str, rate: float):
    _rate_cache[(currency.upper(), date_str)] = (rate, time.time())

def get_historical_exchange_rate(
    from_currency: str,
    to_currency: str = "EUR",
    rate_date: Optional[date] = None
) -> Optional[float]:
    """
    Obtiene tasa de cambio histórica de una fecha específica
    
    Args:
        from_currency: Divisa origen (USD, GBP, CHF, etc.)
        to_currency: Divisa destino (EUR por defecto)
        rate_date: Fecha para la tasa (date object). Si None, usa hoy
        
    Returns:
        float: Tasa de cambio, o None si falla
        
    Examples:
        >>> get_historical_exchange_rate("USD", "EUR", date(2025, 1, 15))
        0.9234
        
        >>> get_historical_exchange_rate("GBP", "EUR", date(2025, 2, 20))
        1.1856
    """
    
    # Si no hay fecha, usar hoy
    if rate_date is None:
        rate_date = datetime.now().date()
    
    # Si la divisa ya es EUR, retornar 1.0
    if from_currency == to_currency:
        return 1.0
    
    # Convertir fecha a string YYYY-MM-DD
    date_str = rate_date.strftime("%Y-%m-%d")

    # PERF-H2: Check cache before API call
    cached = _get_cached_rate(from_currency, date_str)
    if cached is not None:
        return cached

    try:
        # Llamada a frankfurter.app
        url = f"{EXCHANGE_API_URL}/{date_str}"
        params = {
            "from": from_currency.upper(),
            "to": to_currency.upper()
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        # Check si la respuesta es exitosa
        if response.status_code == 200:
            data = response.json()
            rate = data.get("rates", {}).get(to_currency.upper())
            
            if rate:
                result = float(rate)
                _set_cached_rate(from_currency, date_str, result)
                logger.info(f"Tasa {from_currency} -> {to_currency} ({date_str}): {result}")
                return result

        # Si falla, intentar con tasa de hoy
        logger.warning(f"No se encontro tasa para {date_str}, intentando con hoy...")
        return get_current_exchange_rate(from_currency, to_currency)

    except requests.exceptions.Timeout:
        logger.warning("Timeout obteniendo tasa de cambio")
        return get_current_exchange_rate(from_currency, to_currency)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error obteniendo tasa de cambio: {str(e)}")
        return get_current_exchange_rate(from_currency, to_currency)

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return None


def get_current_exchange_rate(
    from_currency: str,
    to_currency: str = "EUR"
) -> Optional[float]:
    """
    Obtiene tasa de cambio actual (última disponible)
    
    Args:
        from_currency: Divisa origen (USD, GBP, CHF, etc.)
        to_currency: Divisa destino (EUR por defecto)
        
    Returns:
        float: Tasa de cambio actual, o None si falla
    """
    
    # Si la divisa ya es EUR, retornar 1.0
    if from_currency == to_currency:
        return 1.0

    # PERF-H2: Check cache
    cached = _get_cached_rate(from_currency, "latest")
    if cached is not None:
        return cached

    try:
        url = f"{EXCHANGE_API_URL}/latest"
        params = {
            "from": from_currency.upper(),
            "to": to_currency.upper()
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            rate = data.get("rates", {}).get(to_currency.upper())
            
            if rate:
                result = float(rate)
                _set_cached_rate(from_currency, "latest", result)
                logger.info(f"Tasa actual {from_currency} -> {to_currency}: {result}")
                return result

        return None

    except Exception as e:
        logger.error(f"Error obteniendo tasa actual: {str(e)}")
        return None


def convert_to_eur(
    amount: float,
    from_currency: str,
    rate_date: Optional[date] = None
) -> Optional[float]:
    """
    Convierte un importe de cualquier divisa a EUR
    
    Args:
        amount: Cantidad a convertir
        from_currency: Divisa origen
        rate_date: Fecha para la tasa (opcional)
        
    Returns:
        float: Cantidad en EUR, o None si falla
        
    Example:
        >>> convert_to_eur(500, "USD", date(2025, 1, 15))
        461.70
    """
    
    if from_currency == "EUR":
        return amount
    
    rate = get_historical_exchange_rate(from_currency, "EUR", rate_date)
    
    if rate:
        return amount * rate
    
    return None


# Test de ejemplo
if __name__ == "__main__":
    print("\n🧪 Testing exchange rate service...\n")
    
    # Test 1: Tasa histórica
    test_date = date(2025, 1, 15)
    rate = get_historical_exchange_rate("USD", "EUR", test_date)
    print(f"Test 1: USD → EUR ({test_date}): {rate}")
    
    # Test 2: Conversión
    amount_usd = 500
    amount_eur = convert_to_eur(amount_usd, "USD", test_date)
    print(f"Test 2: ${amount_usd} → {amount_eur}€")
    
    # Test 3: Tasa actual
    rate_current = get_current_exchange_rate("GBP", "EUR")
    print(f"Test 3: GBP → EUR (hoy): {rate_current}")
    
    print("\n✅ Tests completados")
