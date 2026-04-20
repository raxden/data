#!/usr/bin/env python3
"""
Script para extraer datos históricos de Euribor desde el Banco de Finlandia.
Obtiene las tasas diarias de Euribor 3 meses y las guarda en euribor/data.
"""

import json
import requests
import csv
from io import StringIO
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys


def fetch_euribor_csv_data_by_year(year: int) -> Optional[str]:
    """
    Obtiene los datos de Euribor para un año específico en formato CSV desde el Banco de Finlandia.
    
    Args:
        year: Año a consultar
        
    Returns:
        Contenido CSV o None si hay error
    """
    url = "https://reports.suomenpankki.fi/WebForms/ReportViewerPage.aspx"
    params = {
        'report': '/tilastot/markkina-_ja_hallinnolliset_korot/euriborkorot_pv_chrt_fi',
        'output': 'CSV',
        'paramVuosi': str(year)  # Parámetro para seleccionar el año
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # El CSV viene con BOM UTF-8
        content = response.content.decode('utf-8-sig')
        return content
    except requests.exceptions.RequestException as e:
        print(f"  Error al obtener datos de {year}: {e}")
        return None


def parse_csv_data(csv_content: str) -> List[Dict[str, Any]]:
    """
    Parsea el CSV del Banco de Finlandia y extrae las tasas de Euribor 3 meses.
    
    Args:
        csv_content: Contenido del CSV
        
    Returns:
        Lista de diccionarios con 'date' y 'value'
    """
    all_rates = []
    
    try:
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        for row in csv_reader:
            # Buscar la columna que contiene "3 kk" (3 meses en finlandés)
            period = row.get('dundasChartControl1_DRG_DataRowGrouping1_label', '')
            
            if '3 kk' in period:
                # Extraer fecha y valor
                date_str = row.get('dundasChartControl1_DRG_DataRowGrouping1_dundasChartControl1_DCG_Period1_Value_X', '')
                value_str = row.get('dundasChartControl1_DRG_DataRowGrouping1_dundasChartControl1_DCG_Period1_Value_Y', '')
                
                if date_str and value_str:
                    try:
                        # Parsear la fecha (formato: "11/03/2025 00:00:00" o "MM/DD/YYYY HH:MM:SS")
                        date_obj = datetime.strptime(date_str, '%m/%d/%Y %H:%M:%S')
                        
                        # Parsear el valor
                        value = float(value_str)
                        
                        # Formatear fecha como YYYY-MM-DD
                        date_formatted = date_obj.strftime('%Y-%m-%d')
                        
                        all_rates.append({
                            'date': date_formatted,
                            'value': round(value, 3)
                        })
                        
                    except (ValueError, AttributeError) as e:
                        continue
        
    except Exception as e:
        print(f"Error al parsear CSV: {e}")
        return []
    
    return all_rates


def scrape_euribor_data() -> List[Dict[str, Any]]:
    """
    Extrae datos de Euribor 3 meses desde el Banco de Finlandia.
    Consulta con el año 1999 que incluye todos los datos históricos hasta la fecha actual.
    
    Returns:
        Lista de todas las tasas encontradas
    """
    print("Iniciando extracción de datos de Euribor 3 meses...")
    print("Consultando datos históricos desde 1999...")
    
    # Consultar con año 1999 para obtener todos los datos históricos
    csv_content = fetch_euribor_csv_data_by_year(1999)
    
    if csv_content is None:
        print("Error: No se pudo obtener el CSV")
        return []
    
    # Parsear los datos
    print("Parseando datos del CSV...")
    all_rates = parse_csv_data(csv_content)
    
    print(f"✓ Extracción completada. Total de registros: {len(all_rates)}")
    return all_rates


def create_output_json(daily_rates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Crea el JSON de salida en el formato requerido.
    
    Args:
        daily_rates: Lista de tasas diarias
        
    Returns:
        Diccionario con la estructura final del JSON
    """
    if not daily_rates:
        print("No hay datos para procesar", file=sys.stderr)
        sys.exit(1)
    
    # Ordenar por fecha descendente (más reciente primero)
    daily_rates.sort(key=lambda x: x['date'], reverse=True)
    
    # La fecha más reciente es la primera
    current_date = daily_rates[0]['date']
    
    # Determinar si es provisional (datos del mes actual)
    today = datetime.now()
    current_year_month = f"{today.year:04d}-{today.month:02d}"
    is_provisional = current_date.startswith(current_year_month)
    
    return {
        'current_date': current_date,
        'is_provisional': is_provisional,
        'daily_rates': daily_rates
    }


def save_to_file(data: Dict[str, Any], output_path: Path) -> None:
    """Guarda los datos en el archivo de salida."""
    try:
        # Crear el directorio si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar con formato JSON bonito
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Datos guardados correctamente en {output_path}")
        print(f"  Fecha actual: {data['current_date']}")
        print(f"  Provisional: {data['is_provisional']}")
        print(f"  Total de registros diarios: {len(data['daily_rates'])}")
    except IOError as e:
        print(f"Error al guardar el archivo: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Función principal del script."""
    print("=" * 60)
    print("Extracción de datos históricos de Euribor 3 meses")
    print("Fuente: Banco de Finlandia (Suomen Pankki)")
    print("=" * 60)
    print()
    
    # Determinar la ruta del archivo de salida
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    output_file = project_root / 'euribor' / 'data'
    
    # 1. Extraer datos
    all_rates = scrape_euribor_data()
    
    if not all_rates:
        print("\nError: No se pudieron extraer datos")
        sys.exit(1)
    
    # 2. Crear JSON de salida
    print("\nCreando JSON de salida...")
    output_data = create_output_json(all_rates)
    
    # 3. Guardar en archivo
    save_to_file(output_data, output_file)
    
    print("\n¡Extracción completada exitosamente!")


if __name__ == '__main__':
    main()
