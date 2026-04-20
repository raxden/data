#!/usr/bin/env python3
"""
Scraper para obtener el Euribor diario desde euribordiario.es
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Tuple, Union


def fetch() -> Tuple[str, Union[float, str], str, bool]:
    """
    Intenta obtener el Euribor del día desde euribordiario.es
    Los datos diarios están en un script JSON con id 'chart-data'
    
    Returns:
        Tupla (fecha, valor_o_error, fuente, éxito)
        - Si éxito=True: valor_o_error es float
        - Si éxito=False: valor_o_error es string con el error
    """
    source_name = "euribordiario.es"
    try:
        print(f"Intentando obtener datos de {source_name}...")
        url = "https://www.euribordiario.es/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar el script con id 'chart-data' que contiene el JSON con los datos
        chart_script = soup.find('script', {'id': 'chart-data', 'type': 'application/json'})
        
        if chart_script and chart_script.string:
            # Parsear el JSON
            chart_data = json.loads(chart_script.string)
            
            # Obtener el último valor del array diario.values
            if 'diario' in chart_data and 'values' in chart_data['diario']:
                values = chart_data['diario']['values']
                labels = chart_data['diario']['labels']
                
                if values and len(values) > 0:
                    last_value = values[-1]
                    last_label = labels[-1] if labels and len(labels) > 0 else None
                    
                    # Convertir la fecha del formato "20/4/2026" a "2026-04-20"
                    if last_label:
                        date_parts = last_label.split('/')
                        if len(date_parts) == 3:
                            day, month, year = date_parts
                            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        else:
                            date_str = datetime.now().strftime('%Y-%m-%d')
                    else:
                        date_str = datetime.now().strftime('%Y-%m-%d')
                    
                    print(f"✓ Datos encontrados: {date_str} = {last_value}%")
                    return (date_str, last_value, source_name, True)
        
        error_msg = "Los datos diarios se cargan dinámicamente con JavaScript"
        print(f"  ✗ {error_msg}")
        return (datetime.now().strftime('%Y-%m-%d'), error_msg, source_name, False)
            
    except Exception as e:
        error_msg = str(e)
        print(f"  ✗ Error: {error_msg}")
        return (datetime.now().strftime('%Y-%m-%d'), error_msg, source_name, False)
