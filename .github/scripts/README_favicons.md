# Radio Favicons Processor

Este workflow procesa las estaciones de radio de un país específico y valida/encuentra favicons para cada estación.

## Uso

### Ejecutar manualmente

1. Ve a la pestaña "Actions" en GitHub
2. Selecciona "Radio Favicons Processor"
3. Haz clic en "Run workflow"
4. Introduce el código de país (ej: ES, US, GB, FR, DE)
5. Haz clic en "Run workflow"

### Parámetros

- **countryCode**: Código ISO 3166-1 del país (2 letras, ej: ES para España)

## Funcionamiento

El workflow realiza los siguientes pasos:

1. **Obtiene las estaciones**: Consulta la API de Radio Browser para obtener todas las estaciones del país especificado
   - URL: `https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/[countryCode]`

2. **Valida favicons existentes**: Para cada estación, verifica si el favicon proporcionado:
   - Existe y no está vacío
   - Responde correctamente (no devuelve 4xx, 5xx u otros errores)
   - Es accesible

3. **Busca favicons alternativos** si el favicon original no es válido:
   - Busca en la homepage de la estación:
     - `<link rel="icon">`
     - `<link rel="shortcut icon">`
     - `/favicon.ico` por defecto
     - `<link rel="apple-touch-icon">`
     - `<meta property="og:image">`
   - Utiliza el servicio de favicons de Google como fallback
   - Intenta extraer el favicon del dominio de la URL de streaming

4. **Guarda los resultados**: Crea un archivo JSON en `radio/stations/favicons/[countrycode]` con el formato:
   ```json
   [
       {
           "name": "Nombre de la Radio",
           "url": "https://stream.url/radio",
           "favicon": "https://favicon.url/icon.png"
       }
   ]
   ```

5. **Commit automático**: Si hay cambios, los commitea y pushea al repositorio

## Estructura de salida

Los archivos se guardan en:
```
radio/stations/favicons/
├── es
├── us
├── gb
└── ...
```

Cada archivo contiene un array JSON con las estaciones y sus favicons validados.

## Dependencias

El script Python utiliza:
- `requests`: Para hacer peticiones HTTP
- `beautifulsoup4`: Para parsear HTML y encontrar favicons
- `Pillow`: Para validación de imágenes (si es necesario)

## Estrategia de búsqueda de favicons

1. **Validación del favicon original** de la API
2. **Búsqueda en homepage** (si está disponible)
3. **Google Favicon Service** como fallback
4. **Extracción del dominio de streaming** como último recurso

## Notas

- El script incluye un delay de 0.5 segundos entre estaciones para no sobrecargar los servidores
- Timeout de 10 segundos para cada petición HTTP
- User-Agent configurado para evitar bloqueos
- Manejo robusto de errores para continuar procesando aunque algunas estaciones fallen
