"""
Servicio para obtener tasas de cambio históricas
Usa frankfurter.app - API gratuita sin límites basada en BCE
"""

import requests
from datetime import datetime, date
from typing import Optional

# API gratuita Banco Central Europeo
EXCHANGE_API_URL = "https://api.frankfurter.app"

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
    
    try:
        # Llamada a frankfurter.app
        # Ejemplo: https://api.frankfurter.app/2025-01-15?from=USD&to=EUR
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
                print(f"✅ Tasa {from_currency} → {to_currency} ({date_str}): {rate}")
                return float(rate)
        
        # Si falla, intentar con tasa de hoy
        print(f"⚠️ No se encontró tasa para {date_str}, intentando con hoy...")
        return get_current_exchange_rate(from_currency, to_currency)
        
    except requests.exceptions.Timeout:
        print(f"⚠️ Timeout obteniendo tasa de cambio")
        return get_current_exchange_rate(from_currency, to_currency)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error obteniendo tasa de cambio: {str(e)}")
        # Fallback: usar tasa de hoy
        return get_current_exchange_rate(from_currency, to_currency)
    
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
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
    
    try:
        # Llamada a frankfurter.app (latest)
        # Ejemplo: https://api.frankfurter.app/latest?from=USD&to=EUR
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
                print(f"✅ Tasa actual {from_currency} → {to_currency}: {rate}")
                return float(rate)
        
        return None
        
    except Exception as e:
        print(f"❌ Error obteniendo tasa actual: {str(e)}")
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
