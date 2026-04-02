# Generate Favicons with Logo.dev

Este workflow genera favicons para estaciones de radio utilizando el servicio **Logo.dev API**.

## Diferencia con `find_favicons.yml`

- **find_favicons.yml**: Busca favicons existentes en múltiples fuentes (homepage, servicios externos, etc.)
- **generate_favicons.yml**: Genera URLs de favicon usando Logo.dev API basándose en el dominio de la homepage

## Requisitos previos

### Configurar GitHub Secret

Antes de ejecutar el workflow, debes configurar el token de Logo.dev como secret:

1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Click en "New repository secret"
4. Nombre: `LOGO_TOKEN`
5. Valor: Tu token de Logo.dev (ej: `pk_ZmT_ti_oQiGFau_l8tdg1g`)
6. Click en "Add secret"

⚠️ **Importante**: Sin este secret configurado, el workflow fallará.

## Uso

### Ejecutar manualmente

1. Ve a la pestaña "Actions" en GitHub
2. Selecciona "Generate Favicons with Logo.dev"
3. Haz clic en "Run workflow"
4. **Opcional**: Introduce el código de país (ej: ES, US, GB) o déjalo vacío para procesar todos los países
5. Haz clic en "Run workflow"

### Parámetros

- **countryCode** (opcional): Código ISO 3166-1 del país (2 letras, ej: ES para España)
  - Si se proporciona: procesa solo ese país
  - Si se deja vacío: procesa todos los países

## Funcionamiento

### 1. Extracción del dominio

Para cada estación, el script extrae el dominio de:
- **Primero**: Campo `homepage` de la API
- **Fallback**: Dominio del stream URL si no hay homepage

Ejemplo:
```
homepage: "https://www.radioexample.com/listen"
→ domain: "radioexample.com"
```

### 2. Generación de URL Logo.dev

Construye la URL usando el formato:
```
https://img.logo.dev/{domain}?token=pk_ZmT_ti_oQiGFau_l8tdg1g
```

Ejemplo:
```
domain: "radioexample.com"
→ favicon: "https://img.logo.dev/radioexample.com?token=pk_ZmT_ti_oQiGFau_l8tdg1g"
```

### 3. Validación

Valida que la URL generada responda correctamente:
- Hace una petición HEAD/GET
- Verifica que el código de respuesta sea < 400
- Solo guarda estaciones con favicon válido

### 4. Guardado

Guarda los resultados en:
```
radio/stations/favicons_logodev/{countrycode}
```

Formato JSON:
```json
[
  {
    "name": "Radio Example FM",
    "url": "https://stream.radioexample.com/live",
    "favicon": "https://img.logo.dev/radioexample.com?token=pk_ZmT_ti_oQiGFau_l8tdg1g"
  }
]
```

## Ventajas de Logo.dev

- ✅ **Alta calidad**: Logos vectoriales y de alta resolución
- ✅ **Actualizado**: Base de datos constantemente actualizada
- ✅ **Rápido**: Servicio CDN optimizado
- ✅ **Confiable**: API estable y bien mantenida

## Estadísticas

El script muestra progreso en tiempo real:

```
📊 PROGRESS SUMMARY
  Processed: 100/1000 (10.0%)
  ✓ Success: 85 (85.0%)
  ✗ Failed: 15 (15.0%)
  ⏱️  Elapsed: 0:02:30
  ⏳ Remaining: ~0:22:30
  🎯 ETA: 14:35:00
```

## Salida final

```
✅ PROCESSING COMPLETE
  📁 File: radio/stations/favicons_logodev/es
  📊 Total stations processed: 1000
  ✓ Saved with favicon: 850 (85.0%)
  ✗ Excluded (no favicon): 150 (15.0%)
  ⏱️  Total time: 0:25:00
  ⚡ Avg time/station: 1.50s
```

## Procesamiento paralelo

- **max-parallel: 10** - Procesa hasta 10 países simultáneamente
- **fail-fast: false** - Continúa aunque algún país falle

## Notas

- Solo se guardan estaciones donde Logo.dev tiene un logo disponible
- El token de API está incluido en el script
- Los archivos se guardan en un directorio separado (`favicons_logodev`) para no sobrescribir los favicons encontrados por `find_favicons.yml`
