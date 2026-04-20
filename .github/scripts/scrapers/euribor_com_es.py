#!/usr/bin/env python3
"""
Scraper para obtener el Euribor diario desde euribor.com.es
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Tuple, Union
import re


def fetch() -> Tuple[str, Union[float, str], str, bool]:
    """
    Intenta obtener el Euribor del día desde euribor.com.es
    
    Returns:
        Tupla (fecha, valor_o_error, fuente, éxito)
        - Si éxito=True: valor_o_error es float
        - Si éxito=False: valor_o_error es string con el error
    """
    source_name = "euribor.com.es"
    try:
        print(f"Intentando obtener datos de {source_name}...")
        url = "https://www.euribor.com.es/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar el texto completo de la página
        text = soup.get_text()
        
        # Buscar el patrón específico: "Euríbor hoy: X.XXX%"
        pattern = r'Euríbor hoy:\s*(\d+[.,]\d+)%'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            value_str = match.group(1).replace(',', '.')
            value = float(value_str)
            
            # Validar que el valor esté en un rango razonable para el Euribor
            if 0 <= value <= 10:
                # Usar la fecha actual ya que es el valor del día
                date_str = datetime.now().strftime('%Y-%m-%d')
                
                print(f"✓ Datos encontrados: {date_str} = {value}%")
                return (date_str, value, source_name, True)
        
        error_msg = "No se encontró el patrón 'Euríbor hoy' en la página"
        print(f"  ✗ {error_msg}")
        return (datetime.now().strftime('%Y-%m-%d'), error_msg, source_name, False)
            
    except Exception as e:
        error_msg = str(e)
        print(f"  ✗ Error: {error_msg}")
        return (datetime.now().strftime('%Y-%m-%d'), error_msg, source_name, False)
