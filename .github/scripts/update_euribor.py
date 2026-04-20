#!/usr/bin/env python3
"""
Script para actualizar los datos de Euribor desde la API del BCE.
Transforma los datos mensuales del BCE a formato diario y actualiza el archivo euribor/data.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import sys


def fetch_euribor_data() -> Dict[str, Any]:
    """Obtiene los datos de Euribor desde la API del BCE."""
    url = "https://data-api.ecb.europa.eu/service/data/FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA?format=jsondata"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de la API: {e}", file=sys.stderr)
        sys.exit(1)


def parse_ecb_data(ecb_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parsea los datos del BCE y los convierte a una lista de observaciones mensuales.
    
    Returns:
        Lista de diccionarios con 'date' (YYYY-MM) y 'value' (float)
    """
    try:
        # Navegar por la estructura de datos del BCE
        series_data = ecb_data['dataSets'][0]['series']['0:0:0:0:0:0:0']
        observations = series_data['observations']
        
        # Obtener los períodos de tiempo
        time_periods = ecb_data['structure']['dimensions']['observation'][0]['values']
        
        monthly_data = []
        for idx, period_info in enumerate(time_periods):
            period_id = period_info['id']  # Formato: YYYY-MM
            
            # Verificar si hay datos para este período
            if str(idx) in observations:
                value = observations[str(idx)][0]  # El primer elemento es el valor
                monthly_data.append({
                    'date': period_id,
                    'value': value
                })
        
        return monthly_data
    except (KeyError, IndexError) as e:
        print(f"Error al parsear datos del BCE: {e}", file=sys.stderr)
        sys.exit(1)


def expand_to_daily_rates(monthly_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Expande los datos mensuales a tasas diarias.
    Cada día del mes usa la tasa mensual promedio.
    
    Returns:
        Lista de diccionarios con 'date' (YYYY-MM-DD) y 'value' (float)
    """
    daily_rates = []
    
    for month_data in monthly_data:
        year_month = month_data['date']  # Formato: YYYY-MM
        value = month_data['value']
        
        # Parsear año y mes
        year, month = map(int, year_month.split('-'))
        
        # Calcular el último día del mes
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        
        last_day = (next_month - timedelta(days=1)).day
        
        # Crear una entrada para cada día del mes
        for day in range(1, last_day + 1):
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            daily_rates.append({
                'date': date_str,
                'value': round(value, 3)
            })
    
    # Ordenar por fecha descendente (más reciente primero)
    daily_rates.sort(key=lambda x: x['date'], reverse=True)
    
    return daily_rates


def create_output_json(daily_rates: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Crea el JSON de salida en el formato requerido.
    
    Returns:
        Diccionario con la estructura final del JSON
    """
    if not daily_rates:
        print("No hay datos para procesar", file=sys.stderr)
        sys.exit(1)
    
    # La fecha más reciente es la primera (ordenado descendente)
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
        
        print(f"✓ Datos actualizados correctamente en {output_path}")
        print(f"  Fecha actual: {data['current_date']}")
        print(f"  Provisional: {data['is_provisional']}")
        print(f"  Total de registros diarios: {len(data['daily_rates'])}")
    except IOError as e:
        print(f"Error al guardar el archivo: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Función principal del script."""
    print("Iniciando actualización de datos de Euribor...")
    
    # Determinar la ruta del archivo de salida
    # El script está en .github/scripts/, así que subimos 2 niveles para llegar a la raíz
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    output_file = project_root / 'euribor' / 'data'
    
    # 1. Obtener datos del BCE
    print("1. Obteniendo datos de la API del BCE...")
    ecb_data = fetch_euribor_data()
    
    # 2. Parsear datos mensuales
    print("2. Parseando datos mensuales...")
    monthly_data = parse_ecb_data(ecb_data)
    print(f"   Encontrados {len(monthly_data)} meses de datos")
    
    # 3. Expandir a tasas diarias
    print("3. Expandiendo a tasas diarias...")
    daily_rates = expand_to_daily_rates(monthly_data)
    print(f"   Generados {len(daily_rates)} registros diarios")
    
    # 4. Crear JSON de salida
    print("4. Creando JSON de salida...")
    output_data = create_output_json(daily_rates)
    
    # 5. Guardar en archivo
    print("5. Guardando en archivo...")
    save_to_file(output_data, output_file)
    
    print("\n¡Actualización completada exitosamente!")


if __name__ == '__main__':
    main()
