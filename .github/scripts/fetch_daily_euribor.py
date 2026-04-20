#!/usr/bin/env python3
"""
Script para obtener el Euribor diario desde múltiples fuentes web.
Consulta todas las fuentes y genera dos archivos:
- euribor/data: estructura simple con el primer valor obtenido
- euribor/report: estructura detallada con todos los valores de todas las fuentes
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Union
import sys

# Importar los scrapers
from scrapers import euribordiario, euribor_com_es, expansion


def fetch_all_sources() -> List[Tuple[str, Union[float, str], str, bool]]:
    """
    Intenta obtener el Euribor desde todas las fuentes disponibles.
    Consulta TODAS las fuentes, registrando tanto éxitos como fallos.
    
    Returns:
        Lista de tuplas (fecha, valor_o_error, fuente, éxito) con todos los resultados
    """
    results = []
    
    # Intentar cada fuente (TODAS, sin importar si fallan)
    sources = [
        euribordiario.fetch,
        euribor_com_es.fetch,
        expansion.fetch
    ]
    
    for fetch_func in sources:
        result = fetch_func()
        results.append(result)  # Siempre añadir el resultado (éxito o fallo)
    
    return results


def update_euribor_data(date: str, value: float) -> bool:
    """
    Actualiza el archivo euribor/data con estructura simple.
    Mantiene los datos históricos existentes.
    
    Args:
        date: Fecha en formato YYYY-MM-DD
        value: Valor del Euribor
        
    Returns:
        True si se actualizó correctamente, False en caso contrario
    """
    try:
        # Determinar la ruta del archivo
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        data_file = project_root / 'euribor' / 'data'
        
        print(f"\nActualizando archivo: {data_file}")
        
        # Leer datos existentes
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Si no existe, crear estructura inicial
            data = {
                "current_date": date,
                "is_provisional": True,
                "daily_rates": []
            }
        
        # Verificar si ya existe un registro para esta fecha
        existing_dates = {rate['date'] for rate in data['daily_rates']}
        
        if date in existing_dates:
            print(f"  Ya existe un registro para {date}, actualizando valor...")
            # Actualizar el valor existente
            for rate in data['daily_rates']:
                if rate['date'] == date:
                    rate['value'] = value
                    break
        else:
            print(f"  Añadiendo nuevo registro para {date}...")
            # Añadir nuevo registro al inicio de la lista (estructura simple)
            data['daily_rates'].insert(0, {
                'date': date,
                'value': value
            })
        
        # Actualizar fecha actual
        data['current_date'] = date
        data['is_provisional'] = True
        
        # Guardar datos actualizados
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Archivo euribor/data actualizado")
        print(f"  Fecha: {date}")
        print(f"  Valor: {value}%")
        print(f"  Total de registros: {len(data['daily_rates'])}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error al actualizar euribor/data: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_euribor_report(date: str, sources: List[Tuple[str, Union[float, str], str, bool]]) -> bool:
    """
    Actualiza el archivo euribor/report con información detallada de todas las fuentes.
    Incluye tanto éxitos (con valor) como fallos (con error).
    
    Args:
        date: Fecha en formato YYYY-MM-DD
        sources: Lista de tuplas (fecha, valor_o_error, nombre_fuente, éxito)
    
    Returns:
        True si se actualizó correctamente, False en caso contrario
    """
    try:
        # Determinar la ruta del archivo
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        report_file = project_root / 'euribor' / 'report'
        
        print(f"\nActualizando archivo: {report_file}")
        
        # Leer archivo existente o crear estructura nueva
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                'current_date': date,
                'daily_reports': []
            }
        
        # Preparar lista de fuentes (incluyendo errores)
        source_list = []
        for src_date, value_or_error, src_name, success in sources:
            if success:
                source_list.append({
                    'name': src_name,
                    'value': value_or_error
                })
            else:
                source_list.append({
                    'name': src_name,
                    'error': value_or_error
                })
        
        # Buscar si ya existe un reporte para esta fecha
        existing_report = None
        for report in data['daily_reports']:
            if report['date'] == date:
                existing_report = report
                break
        
        if existing_report:
            print(f"  Ya existe un reporte para {date}, actualizando...")
            existing_report['source'] = source_list
        else:
            print(f"  Añadiendo nuevo reporte para {date}...")
            data['daily_reports'].insert(0, {
                'date': date,
                'source': source_list
            })
        
        # Actualizar fecha actual
        data['current_date'] = date
        
        # Guardar archivo
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Archivo euribor/report actualizado")
        print(f"  Fecha: {date}")
        print(f"  Fuentes consultadas: {len(source_list)}")
        for src in source_list:
            if 'value' in src:
                print(f"    - {src['name']}: {src['value']}%")
            else:
                print(f"    - {src['name']}: ERROR - {src['error']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error al actualizar euribor/report: {e}")
        return False


def main():
    """Función principal del script."""
    print("Iniciando actualización de Euribor diario...\n")
    
    # Obtener datos de todas las fuentes (éxitos y fallos)
    results = fetch_all_sources()
    
    # Filtrar solo los resultados exitosos para euribor/data
    successful_results = [(date, value, source) for date, value, source, success in results if success]
    
    if not successful_results:
        print("\n✗ No se pudo obtener datos de ninguna fuente")
        # Aún así, actualizar el reporte con los errores
        update_euribor_report(datetime.now().strftime('%Y-%m-%d'), results)
        sys.exit(1)
    
    print(f"\n✓ Se obtuvieron datos de {len(successful_results)} fuente(s) exitosa(s)")
    
    # Usar el primer resultado exitoso para actualizar euribor/data
    first_date, first_value, first_source = successful_results[0]
    
    # Actualizar euribor/data (estructura simple)
    data_updated = update_euribor_data(first_date, first_value)
    
    # Actualizar euribor/report (estructura detallada con todas las fuentes)
    report_updated = update_euribor_report(first_date, results)
    
    if data_updated and report_updated:
        print("\n¡Actualización completada exitosamente!")
        sys.exit(0)
    else:
        print("\n✗ Error al actualizar los archivos")
        sys.exit(1)


if __name__ == "__main__":
    main()
