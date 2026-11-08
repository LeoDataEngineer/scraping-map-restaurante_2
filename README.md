# Inteligencia de negocio para restaurantes

Pipeline de extracción, transformación y análisis de reseñas de Google Maps (vía Apify),
más un dashboard interactivo en Streamlit para convertir esos datos en decisiones de negocio.

Todo el análisis es **determinista**: pandas, reglas y expresiones regulares. No usa IA.

## Instalación

Se recomienda usar un entorno virtual para evitar conflictos con otros proyectos:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Estructura del proyecto

```text
scraping-project/
├── src/
│   ├── run_etl.py         # orquestador del pipeline ETL
│   └── etl/
│       ├── extract.py     # extracción desde Apify
│       └── transform.py   # transformación y tablas de negocio
├── app.py                 # dashboard de Streamlit
├── data/
│   ├── raw/               # JSON originales de Apify
│   └── processed/         # 6 tablas CSV listas para consumir
├── docs/                  # análisis de negocio
└── requirements.txt
```

## Pipeline

Ejecutar las dos fases en orden con el orquestador:

```bash
python src/run_etl.py          # extract -> transform
```

O ejecutar cada fase por separado:

```bash
python src/etl/extract.py      # extrae reseñas y perfil desde Apify -> data/raw/
python src/etl/transform.py    # genera las 6 tablas de negocio -> data/processed/
streamlit run app.py           # dashboard
```

### Opciones del orquestador

```bash
python src/run_etl.py --skip-extract     # solo transform, con los raw existentes
python src/run_etl.py --skip-transform   # solo extract
```

El pipeline termina en `data/processed/`. No hay fase de carga a base de datos:
las 6 tablas CSV son la capa de consumo del dashboard y del análisis.

## Agregar restaurantes

1. Abre `src/etl/extract.py` y agrega el `place_id` de Google Maps a la lista `PLACES`.
2. Ejecuta `python src/etl/extract.py`.
3. Ejecuta `python src/etl/transform.py`.
4. Recarga el dashboard. Los restaurantes nuevos aparecen automáticamente en el selector lateral.

## Dashboard (`app.py`)

Se muestra un restaurante a la vez (selector en la barra lateral). Pestañas:

- **Resumen:** KPIs, evolución del rating, distribución de estrellas y alertas automáticas.
- **Satisfacción y reseñas:** comportamiento por estrella, sentimiento y explorador de reseñas.
- **Temas y respuestas:** temas/productos vs. satisfacción, etiquetas de Google, calidad de respuesta y plantillas repetidas.
- **Operación y perfil:** ocupación por día/hora, completitud del perfil de Google y competencia.
- **Plan de acción:** acciones priorizadas con evidencia y rutina semanal/mensual.

La calidad de datos y la descarga de tablas están en la barra lateral.

## Archivos de datos

- `data/raw/`: un JSON por restaurante y día (`<slug>_apify_raw_data_<fecha>.json`).
- `data/processed/`: 6 tablas consolidadas, única fuente del dashboard y del análisis:
  - `restaurants.csv`: una fila por restaurante con todos los KPIs.
  - `reviews.csv`: una fila por reseña, con temas y productos detectados.
  - `monthly_trend.csv`: evolución mensual.
  - `themes.csv`: temas, productos y etiquetas de Google en formato largo.
  - `occupancy.csv`: ocupación por día y hora.
  - `competitors.csv`: benchmark competitivo.
- `docs/analisis_negocio.md`: análisis de negocio narrativo con hallazgos y plan 30/60/90 días.

## Diccionario de datos

Convenciones usadas en las 6 tablas de `data/processed/`:

- **Porcentajes:** número entre `0` y `100` (no fracción). Ej.: `85.5` significa 85,5 %.
- **Fechas:** `YYYY-MM-DD`. **Meses:** `YYYY-MM`. **Horas:** `0`–`23`.
- **Booleanos:** `True` o `False`.
- **Vacío:** el dato no estaba disponible en la fuente.
- **`generated_at`:** fecha y hora local en que se generó cada CSV.

### `restaurants.csv`

Una fila por restaurante. Reúne identificación, KPIs históricos, métricas de la muestra reciente, perfil de Google y ocupación.

#### Identificación y perfil básico

| Columna | Significado |
|---|---|
| `generated_at` | Fecha y hora local en que se generó el CSV. |
| `restaurant_name` | Nombre del restaurante en Google Maps. |
| `place_id` | Identificador único del lugar en Google Maps. |
| `category` | Categoría principal del lugar (ej.: Restaurante, Pizzería). |
| `address` | Dirección completa. |
| `city` | Ciudad. |
| `state` | Estado o provincia. |
| `price_range` | Rango de precio que reporta Google (ej.: `$`, `$$`). |
| `website` | Sitio web del restaurante. |
| `phone` | Teléfono de contacto. |
| `raw_file` | Nombre del JSON de `data/raw/` usado para calcular la fila. |

#### Histórico del perfil de Google

Incluye todas las reseñas que Google reporta en el perfil, no solo la muestra descargada.

| Columna | Significado |
|---|---|
| `total_score_historical` | Calificación promedio histórica del perfil. |
| `reviews_count_historical` | Total de reseñas históricas del perfil. |
| `historical_5star_pct` | Porcentaje histórico de reseñas con 5★. |
| `historical_4star_pct` | Porcentaje histórico con 4★. |
| `historical_3star_pct` | Porcentaje histórico con 3★. |
| `historical_1_2star_pct` | Porcentaje histórico con 1★ o 2★. |
| `nps_proxy_historical` | Proxy de NPS histórico: `% 4–5★ − % 1–2★`. Va de `-100` a `100`. |

#### Muestra reciente descargada de Apify

| Columna | Significado |
|---|---|
| `reviews_sample` | Cantidad de reseñas descargadas en la muestra. |
| `sample_oldest_date` | Fecha de la reseña más antigua de la muestra. |
| `sample_newest_date` | Fecha de la reseña más reciente de la muestra. |
| `days_span` | Días cubiertos por la muestra (desde la más antigua hasta la más reciente). |
| `reviews_per_day` | Promedio de reseñas por día: `reviews_sample / days_span`. |
| `reviews_per_month` | Promedio estimado de reseñas por mes (usa 30 días). |

#### Calificaciones de la muestra reciente

| Columna | Significado |
|---|---|
| `recent_avg_rating` | Promedio de estrellas de la muestra. |
| `recent_5star_pct` | Porcentaje de 5★ en la muestra. |
| `recent_4star_pct` | Porcentaje de 4★ en la muestra. |
| `recent_3star_pct` | Porcentaje de 3★ en la muestra. |
| `recent_1_2star_pct` | Porcentaje de 1★ o 2★ en la muestra. |
| `nps_proxy_recent` | Proxy de NPS de la muestra: `% 4–5★ − % 1–2★`. |
| `rating_delta_recent_vs_historical` | `recent_avg_rating − total_score_historical`. Positivo indica mejora reciente. |

#### Comportamiento de las reseñas

| Columna | Significado |
|---|---|
| `pct_with_text` | Porcentaje de reseñas con texto. |
| `pct_5star_without_text` | Porcentaje de reseñas de 5★ sin texto, dentro de las 5★. |
| `pct_4_5star_without_text` | Porcentaje de reseñas de 4–5★ sin texto, dentro de las 4–5★. |
| `pct_with_photo` | Porcentaje de reseñas con al menos una foto. |
| `avg_photos_per_review` | Promedio de fotos por reseña. |
| `pct_local_guide` | Porcentaje de reseñas escritas por Local Guides. |
| `median_reviewer_reviews` | Mediana del número de reseñas que ha escrito cada autor. |
| `pct_with_detailed_rating` | Porcentaje con al menos una subcalificación (comida, servicio o ambiente). |
| `avg_food_rating` | Promedio de la subcalificación de comida (1–5). |
| `avg_service_rating` | Promedio de la subcalificación de servicio (1–5). |
| `avg_ambience_rating` | Promedio de la subcalificación de ambiente (1–5). |

#### Respuesta del propietario

| Columna | Significado |
|---|---|
| `owner_response_rate` | Porcentaje de reseñas con respuesta del propietario. |
| `owner_response_rate_1_2star` | Porcentaje de reseñas de 1–2★ que recibieron respuesta. |
| `owner_response_rate_1_3star` | Porcentaje de reseñas de 1–3★ que recibieron respuesta. |
| `replied` | Cantidad de reseñas respondidas. |
| `reviews_1_2star` | Cantidad de reseñas de 1–2★. |
| `replied_1_2star` | Cantidad de reseñas de 1–2★ respondidas. |
| `reviews_1_3star` | Cantidad de reseñas de 1–3★. |
| `replied_1_3star` | Cantidad de reseñas de 1–3★ respondidas. |
| `generic_replies` | Cantidad de respuestas genéricas (solo agradecimiento o plantilla). |
| `generic_reply_pct` | Porcentaje de respuestas genéricas sobre las respondidas. |
| `repeated_replies` | Cantidad de respuestas cuyo texto exacto se repite 2 o más veces. |
| `repeated_reply_pct` | Porcentaje de respuestas repetidas sobre las respondidas. |
| `named_replies` | Cantidad de respuestas que mencionan el primer nombre del autor. |
| `named_reply_pct` | Porcentaje de respuestas personalizadas sobre las respondidas. |
| `avg_reply_length` | Longitud promedio de las respuestas, en caracteres. |

#### Idioma de las reseñas

| Columna | Significado |
|---|---|
| `pct_spanish` | Porcentaje de reseñas en español. |
| `pct_english` | Porcentaje de reseñas en inglés. |
| `pct_other_language` | Porcentaje en otros idiomas; incluye reseñas sin idioma detectado. |

#### Completitud del perfil de Google

| Columna | Significado |
|---|---|
| `profile_score` | Porcentaje de completitud del perfil según 11 campos clave. |
| `missing_profile_fields` | Campos faltantes, separados por coma (ej.: `sitio web, menú`). |
| `has_price` | `True` si tiene rango de precio. |
| `has_website` | `True` si tiene sitio web. |
| `has_menu` | `True` si tiene menú. |
| `has_hours` | `True` si tiene horarios. |
| `has_description` | `True` si tiene descripción del propietario. |
| `has_phone` | `True` si tiene teléfono. |
| `has_photos` | `True` si tiene fotos. |
| `has_attributes` | `True` si tiene atributos adicionales. |
| `has_service_options` | `True` si tiene opciones de servicio (comer allí, para llevar, delivery, etc.). |
| `has_reservations` | `True` si tiene información de planificación o reservas. |
| `has_payments` | `True` si tiene métodos de pago. |
| `additional_info_groups` | Cantidad de grupos de información adicional del perfil. |
| `additional_attributes` | Cantidad total de atributos adicionales. |
| `images_count` | Cantidad de imágenes del perfil de Google. |

#### Ocupación estimada (Google Popular Times)

| Columna | Significado |
|---|---|
| `peak_hour` | Hora con mayor ocupación promedio (`0`–`23`). |
| `peak_hour_avg_occupancy_pct` | Ocupación promedio en la hora pico. |
| `busiest_day` | Día de la semana con mayor ocupación promedio. |
| `busiest_day_avg_occupancy_pct` | Ocupación promedio en el día más concurrido. |
| `dead_hours_lt25` | Horas con ocupación promedio menor a 25 %, separadas por coma. |
| `avg_occupancy_pct` | Ocupación promedio general. |

#### Calidad de los datos

| Columna | Significado |
|---|---|
| `pct_with_review_id` | Porcentaje de reseñas con identificador único. Mide la calidad de la extracción. |
| `pct_with_language` | Porcentaje de reseñas con idioma detectado. |

### `reviews.csv`

Una fila por reseña descargada.

| Columna | Significado |
|---|---|
| `restaurant_name` | Nombre del restaurante. |
| `place_id` | Identificador del lugar en Google Maps. |
| `review_id` | Identificador único de la reseña (puede faltar). |
| `author` | Nombre del autor de la reseña. |
| `rating` | Calificación en estrellas (1–5). |
| `sentiment` | Sentimiento proxy por estrellas: `Positivo` (4–5), `Neutro` (3), `Negativo` (1–2). |
| `publish_time` | Fecha y hora original de publicación (ISO 8601, UTC). |
| `publish_date` | Fecha de publicación (`YYYY-MM-DD`). |
| `year_month` | Año y mes de publicación (`YYYY-MM`). |
| `language` | Código de idioma (`es`, `en`, etc.). Vacío si no se detectó. |
| `review_text` | Texto limpio de la reseña. |
| `text_length` | Longitud del texto en caracteres. |
| `has_text` | `True` si la reseña tiene texto. |
| `likes_count` | Cantidad de “me gusta” de la reseña. |
| `photos_count` | Cantidad de fotos adjuntas a la reseña. |
| `is_local_guide` | `True` si el autor es Local Guide. |
| `reviewer_reviews` | Cantidad de reseñas escritas por el autor. |
| `owner_replied` | `True` si el propietario respondió. |
| `owner_reply_text` | Texto de la respuesta del propietario. |
| `food_rating` | Subcalificación de comida (1–5). |
| `service_rating` | Subcalificación de servicio (1–5). |
| `ambience_rating` | Subcalificación de ambiente (1–5). |
| `topics` | Temas detectados por palabras clave, separados por `; `. |
| `products` | Productos detectados por palabras clave, separados por `; `. |

### `monthly_trend.csv`

Una fila por restaurante y mes.

| Columna | Significado |
|---|---|
| `restaurant_name` | Nombre del restaurante. |
| `year_month` | Mes (`YYYY-MM`). |
| `is_partial_month` | `True` si es el mes actual en curso; sus cifras están incompletas. |
| `reviews` | Cantidad de reseñas de la muestra publicadas ese mes. |
| `avg_rating` | Promedio de estrellas del mes. |
| `pct_1_3star` | Porcentaje de reseñas de 1–3★ (insatisfacción). |
| `pct_4_5star` | Porcentaje de reseñas de 4–5★ (satisfacción). |
| `pct_with_text` | Porcentaje de reseñas con texto. |
| `pct_with_reply` | Porcentaje de reseñas con respuesta del propietario. |
| `avg_text_length` | Longitud promedio del texto, en caracteres. |
| `pct_with_photo` | Porcentaje de reseñas con foto. |

### `themes.csv`

Una fila por restaurante y etiqueta analizada. El campo `dimension` indica el tipo de etiqueta.

| Columna | Significado |
|---|---|
| `restaurant_name` | Nombre del restaurante. |
| `dimension` | Tipo de etiqueta: `Tema`, `Producto` o `Etiqueta Google`. |
| `label` | Nombre del tema, producto o etiqueta de Google. |
| `mentions` | Menciones del label en reseñas con texto. En etiquetas de Google es el conteo que reporta Google. |
| `pct_of_text_reviews` | Porcentaje de reseñas con texto que mencionan el label. Vacío en etiquetas de Google. |
| `avg_rating` | Promedio de estrellas de las reseñas que mencionan el label. Vacío en etiquetas de Google. |
| `rating_gap_vs_restaurant` | `avg_rating` del label menos el promedio del restaurante. Positivo indica que el label rinde mejor que la media. |
| `pct_positive` | Porcentaje de reseñas del label con 4–5★. Vacío en etiquetas de Google. |
| `pct_negative` | Porcentaje de reseñas del label con 1–2★. Vacío en etiquetas de Google. |
| `rank` | Posición de la etiqueta de Google (`1` = la más mencionada). Vacío en temas y productos. |
| `sample_rating` | Estrellas de la reseña de ejemplo más reciente. |
| `sample_date` | Fecha de la reseña de ejemplo. |
| `sample_verbatim` | Primeros 300 caracteres de la reseña de ejemplo. |

### `occupancy.csv`

Una fila por restaurante, día de la semana y hora.

| Columna | Significado |
|---|---|
| `restaurant_name` | Nombre del restaurante. |
| `day` | Día de la semana en español (`Lunes` a `Domingo`). |
| `hour` | Hora del día (`0`–`23`). |
| `occupancy_pct` | Ocupación estimada por Google Popular Times (`0`–`100`). No representa ventas reales. |

### `competitors.csv`

Una fila por restaurante y competidor sugerido por Google.

| Columna | Significado |
|---|---|
| `restaurant_name` | Nombre del restaurante analizado. |
| `competitor_name` | Restaurante que Google sugiere como relacionado. |
| `competitor_reviews` | Total de reseñas del competidor. |
| `competitor_rating` | Calificación promedio del competidor. |

## Notas

- La muestra son las reseñas que devuelve Apify según `maxReviews` (hasta 2000 por restaurante con la configuración actual). Si el lugar tiene menos reseñas que ese límite, la muestra coincide con el historial completo (es el caso de ORNO: 1.897 de 1.897).
- El sentimiento es un proxy por estrellas: 4–5 positivo, 3 neutro, 1–2 negativo.
- Los temas y productos se detectan por palabras clave; puede haber falsos positivos/negativos.
- La ocupación es la estimación de Google (popular times), no ventas reales.
- Para medir impacto económico hace falta integrar POS/reservas/delivery.
