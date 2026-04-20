#!/usr/bin/env python3
"""
Scraper para obtener el Euribor diario desde expansion.com
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Tuple, Union
import re


def fetch() -> Tuple[str, Union[float, str], str, bool]:
    """
    Intenta obtener el Euribor del día desde expansion.com
    
    Returns:
        Tupla (fecha, valor_o_error, fuente, éxito)
        - Si éxito=True: valor_o_error es float
        - Si éxito=False: valor_o_error es string con el error
    """
    source_name = "expansion.com"
    try:
        print(f"Intentando obtener datos de {source_name}...")
        url = "https://www.expansion.com/mercados/euribor.html"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar la tabla con los datos históricos (segunda tabla)
        tables = soup.find_all('table')
        
        if len(tables) >= 2:
            # La segunda tabla contiene el histórico con fechas y valores
            table = tables[1]
            rows = table.find_all('tr')
            
            # La primera fila después del encabezado tiene el dato más reciente
            if len(rows) >= 2:
                cells = rows[1].find_all('td')
                if len(cells) >= 2:
                    # Primera celda: fecha (formato DD/MM/YYYY)
                    date_text = cells[0].get_text(strip=True)
                    date_match = re.match(r'(\d{2})/(\d{2})/(\d{4})', date_text)
                    
                    # Segunda celda: valor
                    value_text = cells[1].get_text(strip=True)
                    value_match = re.search(r'(\d+[.,]\d+)', value_text)
                    
                    if date_match and value_match:
                        day, month, year = date_match.groups()
                        date_str = f"{year}-{month}-{day}"
                        
                        value_str = value_match.group(1).replace(',', '.')
                        value = float(value_str)
                        
                        print(f"✓ Datos encontrados: {date_str} = {value}%")
                        return (date_str, value, source_name, True)
        
        error_msg = "No se encontró el valor del Euribor en las tablas"
        print(f"  ✗ {error_msg}")
        return (datetime.now().strftime('%Y-%m-%d'), error_msg, source_name, False)
            
    except Exception as e:
        error_msg = str(e)
        print(f"  ✗ Error: {error_msg}")
        return (datetime.now().strftime('%Y-%m-%d'), error_msg, source_name, False)
