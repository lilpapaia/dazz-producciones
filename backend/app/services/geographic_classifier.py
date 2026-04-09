"""
Clasificador geográfico para facturas
Clasifica países en: NACIONAL, UE, INTERNACIONAL
"""

# NACIONAL: Solo España peninsular + Baleares
NACIONAL_CODES = ['ES']

# UE: Canarias + Resto Unión Europea
# Nota: Canarias tiene código especial 'IC' (Islas Canarias)
UE_CODES = [
    'IC',  # Canarias (zona especial fiscal UE)
    'AT',  # Austria
    'BE',  # Bélgica
    'BG',  # Bulgaria
    'HR',  # Croacia
    'CY',  # Chipre
    'CZ',  # República Checa
    'DK',  # Dinamarca
    'EE',  # Estonia
    'FI',  # Finlandia
    'FR',  # Francia
    'DE',  # Alemania
    'GR',  # Grecia
    'HU',  # Hungría
    'IE',  # Irlanda
    'IT',  # Italia
    'LV',  # Letonia
    'LT',  # Lituania
    'LU',  # Luxemburgo
    'MT',  # Malta
    'NL',  # Países Bajos
    'PL',  # Polonia
    'PT',  # Portugal
    'RO',  # Rumanía
    'SK',  # Eslovaquia
    'SI',  # Eslovenia
    'SE',  # Suecia
]

# INTERNACIONAL: Resto del mundo
# No necesita lista, es cualquier otro país

# Nombres de países para display (opcional)
COUNTRY_NAMES = {
    'ES': 'España',
    'IC': 'Canarias',
    'US': 'Estados Unidos',
    'GB': 'Reino Unido',
    'UK': 'Reino Unido',  # Alias
    'CH': 'Suiza',
    'FR': 'Francia',
    'DE': 'Alemania',
    'IT': 'Italia',
    'PT': 'Portugal',
    'NL': 'Países Bajos',
    'BE': 'Bélgica',
    'AT': 'Austria',
    'SE': 'Suecia',
    'DK': 'Dinamarca',
    'FI': 'Finlandia',
    'NO': 'Noruega',
    'PL': 'Polonia',
    'CZ': 'República Checa',
    'HU': 'Hungría',
    'RO': 'Rumanía',
    'BG': 'Bulgaria',
    'HR': 'Croacia',
    'GR': 'Grecia',
    'CY': 'Chipre',
    'MT': 'Malta',
    'LU': 'Luxemburgo',
    'IE': 'Irlanda',
    'SI': 'Eslovenia',
    'SK': 'Eslovaquia',
    'EE': 'Estonia',
    'LV': 'Letonia',
    'LT': 'Lituania',
    'CA': 'Canadá',
    'MX': 'México',
    'BR': 'Brasil',
    'AR': 'Argentina',
    'CL': 'Chile',
    'CO': 'Colombia',
    'JP': 'Japón',
    'CN': 'China',
    'IN': 'India',
    'AU': 'Australia',
    'NZ': 'Nueva Zelanda',
    'ZA': 'Sudáfrica',
    'AE': 'Emiratos Árabes',
    'SA': 'Arabia Saudita',
    'TR': 'Turquía',
    'RU': 'Rusia',
    'UA': 'Ucrania',
}


def classify_geography(country_code: str) -> str:
    """
    Clasifica un país en: NACIONAL, UE, o INTERNACIONAL
    
    Args:
        country_code: Código ISO de 2 letras del país (ES, US, FR, etc.)
        
    Returns:
        str: 'NACIONAL', 'UE', o 'INTERNACIONAL'
        
    Examples:
        >>> classify_geography('ES')
        'NACIONAL'
        
        >>> classify_geography('IC')  # Canarias
        'UE'
        
        >>> classify_geography('FR')
        'UE'
        
        >>> classify_geography('US')
        'INTERNACIONAL'
    """
    
    if not country_code:
        return 'NACIONAL'  # Default si no hay código
    
    country_code = country_code.upper().strip()
    
    # Nacional: Solo España
    if country_code in NACIONAL_CODES:
        return 'NACIONAL'
    
    # UE: Canarias + resto UE
    if country_code in UE_CODES:
        return 'UE'
    
    # Internacional: Todo lo demás
    return 'INTERNACIONAL'


def get_country_name(country_code: str) -> str:
    """
    Obtiene el nombre del país desde su código
    
    Args:
        country_code: Código ISO de 2 letras
        
    Returns:
        str: Nombre del país, o el código si no se encuentra
        
    Example:
        >>> get_country_name('US')
        'Estados Unidos'
    """
    
    if not country_code:
        return 'España'  # Default
    
    country_code = country_code.upper().strip()
    return COUNTRY_NAMES.get(country_code, country_code)


def is_iva_reclamable(country_code: str) -> bool:
    """
    Determina si el IVA de un país es reclamable
    
    Args:
        country_code: Código ISO de 2 letras
        
    Returns:
        bool: True si es reclamable (UE o Internacional)
        
    Example:
        >>> is_iva_reclamable('ES')
        False  # Nacional, no reclamable
        
        >>> is_iva_reclamable('FR')
        True  # UE, reclamable
        
        >>> is_iva_reclamable('US')
        True  # Internacional, reclamable
    """
    
    classification = classify_geography(country_code)
    
    # Solo NACIONAL no es reclamable
    return classification != 'NACIONAL'
