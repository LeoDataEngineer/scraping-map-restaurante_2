# Análisis de negocio: ORNO Guatemala (Palermo, Buenos Aires)

Restaurante analizado: **ORNO Guatemala** (ORNO Cantina) — Guatemala 4701 PB, C1425 Cdad. Autónoma de Buenos Aires.
Fuente: `data/raw/orno_guatemala_apify_raw_data_2026-11-07.json` con **1.897 reseñas**, que equivalen al **100% del historial** que reporta el perfil de Google (`reviewsCount = 1.897`).
Salida: 6 tablas en `data/processed/` (`restaurants`, `reviews`, `monthly_trend`, `themes`, `occupancy`, `competitors`).

> **Cómo leer las cifras.** A diferencia de análisis anteriores, aquí la muestra **no es un corte parcial**: Apify descargó las 1.897 reseñas que Google reporta como total histórico. Por eso "histórico" y "muestra" coinciden (rating 4,5 vs. 4,52; NPS proxy 81,71 en ambos). El periodo cubierto va de **2022-12-02 a 2026-11-07** (1.437 días).

---

## 1. Resumen ejecutivo

- **ORNO es un caso de éxito reciente, no un restaurante parejo en el tiempo.** El rating pasó de **4,24 en 2023** y **4,22 en 2024** a **4,68 en 2025** y **4,58 en 2026**. La insatisfacción dura (1–2★) cayó de **15,51% a 3,55%** entre 2023 y 2025.
- **El volumen también cambió de escala**: de ~280 reseñas/año en 2023–2024 a **818 en 2025**, con picos de 190 (junio), 182 (julio) y 160 (agosto). En 2026 el ritmo se normalizó a 19–58 por mes.
- **La respuesta del dueño es el mejor indicador de madurez operativa**: pasó de **7,26% en 2023** a **96,21% en 2025** y **91,48% en 2026**. La calidad también es alta: 84,59% de respuestas nombran al autor y el largo medio es de 217 caracteres.
- **El riesgo principal es precio/valor**: 134 menciones, rating **3,60**, gap **−0,92★** y **25,37% negativas**. Es el único tema masivo con rating bajo 4,0. En octubre 2026 reaparece con fuerza (pizza a $35.000, Detroit a $49.000, lata de Coca a $8.500).
- **El dolor operativo oculto es la espera**: 58 menciones, rating **2,59**, gap **−1,93★** y **51,72% negativas**. Empeoró en 2026 (2,38; 62,50% negativas) tras haber mejorado en 2025 (3,47).
- **La pizza es la bandera pero la ejecución es despareja**: Pizza 4,32 (−0,20★), Detroit 4,28, Napolitana 4,17, Margarita 4,16, Porteña 4,00. La masa y el punto de cocción aparecen tanto en elogios como en quejas.
- **Los productos héroe existen y son diferenciales**: **Mora 4,96 con 0% negativas**, Pera 4,67, Stracciatella 4,56, Bingo 4,55, Vermouth 4,25. La etiqueta de Google más repetida después de "pizza estilo detroit" es justamente **"mora"** y **"peras"**.
- **El equipo es la marca**: Oriana aparece en **273 reseñas** (rating 4,89, 0% negativas), Facundo en 41 (4,98) y Salomé en 7 (5,00). La etiqueta N.º 1 de Google es el nombre **"oriana gonzález marzoli"** (72 menciones), por encima de "pizza estilo detroit" (70).
- **La oportunidad de capacidad está en el almuerzo**: ocupación media 42,2%, cena 19–23 h ≈ **55,7%** vs. almuerzo 12–15 h ≈ **25,3%**. Las horas 12 y 13 son las únicas por debajo de 25%.
- **Delivery es pequeño pero severo**: 11 menciones, rating **1,91** y **81,82% negativas** (frío, packaging, faltantes). No mueve la aguja hoy, pero es una fuga de marca.
- **El perfil de Google está al 100%** en los 11 campos clave. La única corrección de fondo es la **categoría: dice "Restaurante", no "Pizzería"**, y la web usa `http` en lugar de `https`.

---

## 2. Qué datos tienes (activos analíticos)

### A nivel de restaurante — `restaurants.csv` (1 fila × 84 columnas)
- Identidad y perfil: nombre, `place_id`, categoría, dirección, ciudad, web, teléfono, rango de precio, `raw_file`, `generated_at`.
- Histórico de Google: `total_score_historical`, `reviews_count_historical`, distribución completa por estrellas y NPS proxy histórico.
- Muestra: rating, distribución, velocidad (`reviews_per_day`, `reviews_per_month`), periodo cubierto, idioma, fotos, Local Guides, rating detallado.
- Respuesta del dueño: cobertura global, a 1–2★, a 1–3★, genéricas, repetidas, con nombre y largo medio.
- Salud del perfil: `profile_score`, campos presentes/ausentes, atributos e imágenes.
- Resumen de ocupación: hora pico, día más ocupado, horas valle y ocupación media.

### A nivel de reseña — `reviews.csv` (1 fila por reseña, 24 columnas)
- Estrellas, texto, fecha, `year_month`, idioma, likes, fotos, `is_local_guide`, reseñas previas del autor.
- `sentiment` (proxy determinista por estrellas: 4–5★ positivo, 3★ neutro, 1–2★ negativo).
- `topics` y `products` detectados por regex (separados por `;`).
- Respuesta del dueño (`owner_replied`, `owner_reply_text`).
- `food_rating`, `service_rating`, `ambience_rating`.

### Tablas derivadas
- `monthly_trend.csv`: evolución mensual (rating, volumen, % 1–3★, texto, respuesta, fotos).
- `themes.csv`: temas, productos y etiquetas de Google en formato largo con `dimension`, `label`, `mentions`, rating, gap vs. media y verbatim de ejemplo.
- `occupancy.csv`: ocupación estimada (popular times) por día y hora, **solo en horarios de apertura**.
- `competitors.csv`: benchmark de reseñas y rating de competidores.

### Lo que **no** tienes todavía
- Fechas de respuesta del dueño → no se puede medir tiempo de respuesta.
- `visitedIn` vacío → no se sabe si la visita fue almuerzo, after office o cena (la ocupación sí distingue franjas).
- Ventas, ticket promedio, margen por plato, reservas y delivery propios → sin esto no se puede cuantificar el impacto en ingresos.
- Ocupación de martes y del almuerzo del lunes (Google no devuelve datos) → hay que validarlo operativamente.

---

## 3. Snapshot del restaurante

| Métrica | Valor |
|---|---:|
| Rating histórico | 4,5 |
| Rating de la muestra (n=1.897) | 4,52 |
| Volumen histórico | 1.897 reseñas (100% del perfil) |
| Periodo de la muestra | dic 2022 → nov 2026 (1.437 días) |
| Velocidad | 1,32/día (~39,6/mes) |
| 5★ | 74,28% |
| 4★ | 14,23% |
| 3★ | 4,69% |
| 1–2★ | 6,80% |
| NPS proxy | 81,71 |
| Reseñas con texto | 79,49% (1.508) |
| Reseñas con foto | 15,87% (301) |
| Local Guides | 48,55% (921) |
| Rating detallado disponible | 87,14% |
| Comida / Servicio / Ambiente | 4,55 / 4,66 / 4,63 |
| Texto: mediana / media | 68 / 118,5 caracteres |
| Respuesta del dueño | 69,79% (1.324) |
| Respuesta a 1–2★ | 57,36% (74/129) |
| Respuesta a 1–3★ | 55,96% (122/218) |
| Respuestas con nombre | 84,59% |
| Respuestas genéricas | 10,80% |
| Respuestas con texto exacto repetido | 5,66% |
| Largo medio de respuesta | 217,1 caracteres |
| Español / Inglés / Otro | 92,73 / 3,85 / 3,43% |
| Score del perfil de Google | 100,0% |
| Categoría actual | Restaurante (debería ser Pizzería) |
| Hora pico | 21:00 (66,7%) |
| Día más ocupado | Sábado (59,9%) |
| Ocupación media | 42,2% |
| Horas valle (<25%) | 12, 13 |

Lectura: **ORNO tiene un producto y un equipo de nivel alto, un perfil impecable y una operación de respuesta madura**. Lo que lo separa de un 4,7 sostenido no es la experiencia base: es la **percepción de precio** y la **consistencia en hora pico**.

---

## 4. Evolución: el salto de 2025

| Año | Reseñas | Rating | 1–2★ | Con texto | Respuesta | Respuesta a 1–2★ |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 303 | 4,24 | 15,51% | 82,18% | 7,26% | 36,17% (17/47) |
| 2024 | 282 | 4,22 | 10,28% | 74,11% | 22,34% | 37,93% (11/29) |
| 2025 | 818 | 4,68 | 3,55% | 78,85% | 96,21% | 86,21% (25/29) |
| 2026 (a nov 7) | 493 | 4,58 | 4,87% | 81,95% | 91,48% | 87,50% (21/24) |

> 2022 solo tiene 1 reseña (5★, respondida); se omite de la tabla por falta de representatividad.

**Qué cambió en 2025.** No fue solo marketing: coinciden tres cosas a la vez —más volumen (818 reseñas), mejor rating (4,68) y respuesta casi total (96,21%). El patrón sugiere una operación distinta: más capacidad, mejor servicio y una gestión activa de la reputación. La caída de 1–2★ de 15,51% a 3,55% es el dato más contundente.

**Qué mirar en 2026.** El rating se sostiene (4,58) pero aparecen dos meses flojos:
- **Octubre 2026**: 46 reseñas, **4,24**, **23,91% de 1–3★**. El mes más débil del año, traccionado por quejas de precio y pizzas frías/poco cocidas.
- **Marzo 2026**: 44 reseñas, 4,41, 18,18% de 1–3★.

No es una tendencia estructural todavía, pero es la señal para auditar la operación de los fines de semana y la comunicación de precios.

---

## 5. Hallazgos clave y valor para el negocio

### 5.1 Precio/valor: el riesgo más rentable de atacar
- **134 menciones (8,89% de las reseñas con texto), rating 3,60, gap −0,92★, 25,37% negativas.** Es el único tema de alto volumen por debajo de 4,0.
- La evolución no mejora: 2023 → 3,40 (36,67% negativas); 2024 → 3,33 (27,78%); 2025 → 3,97 (18,75%); **2026 → 3,69 (19,44%)**.
- Las quejas son concretas y repetibles: pizza individual a **$35.000**, Detroit de 4 porciones a **$49.000**, lata de Coca a **$8.500**, vermut con sifón para 3. El problema no es solo el nivel de precio: es la **relación precio-porción percibida** y la **falta de contexto** (no se explica el tamaño ni qué incluye).
- **Valor:** revisar menu engineering y, sobre todo, **comunicar porciones y formato**. Ajustar la carta para anclar el valor (combos, opciones por porción, guarniciones) puede recuperar 0,3–0,5★ en el segmento que castiga el valor sin bajar el ticket.

### 5.2 Espera y demora: el dolor operativo que reaparece
- **58 menciones (3,85%), rating 2,59, gap −1,93★, 51,72% negativas.** Es el peor gap de todos los temas.
- La serie por año cuenta una historia clara: **2023 2,09 (68,18% negativas) → 2024 2,54 (46,15%) → 2025 3,47 (26,67%) → 2026 2,38 (62,50%)**. La mejora de 2025 se revirtió.
- En 2026 la espera aparece junto a la pizza fría o poco cocida: es un problema de **sincronización cocina-sala en hora pico**, no de amabilidad.
- **Valor:** mapear tiempos por franja (21–22 h es el pico), revisar capacidad de horno y expeditación, y definir un estándar de comunicación al cliente cuando la demora supera X minutos. Es una acción de operación, barata y de impacto directo en rating.

### 5.3 La pizza es la bandera, pero la ejecución es despareja
- **Pizza: 537 menciones, 4,32, −0,20★, 10,06% negativas.** Es el producto más mencionado y el centro de la identidad.
- Por estilo: **Detroit 4,28** (104 menciones), **Napolitana 4,17** (64), **Margarita 4,16** (32), **Porteña 4,00** (12). La Fainá, compañera clásica, queda en **4,18 con 13,64% negativas**.
- Los elogios se concentran en masa, borde y sabor; las quejas, en **punto de cocción, temperatura al llegar a la mesa y tamaño vs. precio**.
- **Valor:** estandarizar receta y punto por estilo, y auditar la salida de horno en las horas de mayor volumen. La pizza no necesita reinvención: necesita **consistencia**.

### 5.4 Productos héroe: Mora, Pera, Stracciatella y Bingo
- **Mora: 51 menciones, 4,96, 0% negativas.** Es el producto con mejor rating de toda la carta y una etiqueta fuerte de Google (27 menciones).
- **Pera: 24 menciones, 4,67** (etiqueta Google: 24). **Stracciatella: 18, 4,56.** **Bingo: 20, 4,55** (etiqueta Google: 16). **Vermouth: 8, 4,25.**
- La pizza **Detroit de peras** aparece en reseñas como recomendación explícita ("pedir la denver de peras"). Hay un diferencial de producto real, no inventado por el marketing.
- **Valor:** estos productos deberían estar **más arriba en la carta, en el menú de Google y en el guion de sugerencia del salón**. Son la prueba de que ORNO puede cobrar precio premium cuando el valor percibido es alto.

### 5.5 El equipo es la marca (y el mejor activo de reputación)
- **Oriana: 273 menciones, rating 4,89, 0% negativas** (157 en 2025, 116 en 2026). Es, literalmente, la etiqueta N.º 1 de Google.
- **Facundo: 41 menciones, 4,98, 0% negativas.** **Salomé: 7 menciones, 5,00.**
- El tema **Servicio y atención** es el más mencionado: 869 reseñas (57,63%), rating **4,63**, gap **+0,11★**, 91,37% positivas.
- **Valor:** formalizar lo que ya funciona (protocolo de bienvenida, nombre al cliente, recomendación de productos) y usarlo en la respuesta pública y en la captación de talento. El riesgo es de **dependencia de personas clave**: si Oriana o Facundo no están, la experiencia no debe caer.

### 5.6 Respuesta del dueño: excelente en el presente, deuda en el pasado
- Cobertura global **69,79%** y a 1–2★ **57,36%**. El número parece bajo, pero se explica por la historia: **antes de 2025 casi no había respuestas** (7,26% en 2023, 22,34% en 2024).
- **Las 48 reseñas de 1–2★ sin responder son de 2023–2024** (30 en 2023 + 18 en 2024). Responderlas subiría la cobertura de 1–2★ a **94,57%** (122/129) y la global a ~72,3%.
- La calidad es buena: **84,59% con nombre**, solo **10,80% genéricas**, **5,66% repetidas** y 217 caracteres de media.
- Para llegar a 90% global harían falta ~383 respuestas más, casi todas de reseñas positivas antiguas. **No es la prioridad.**
- Ojo con el snapshot: la caída de respuesta en meses recientes (jul 86,54%, ago 75,00%, sep 68,97%, oct 80,43%, nov 78,95%) puede reflejar reseñas todavía sin responder, no un abandono del hábito.
- **Valor:** mantener el SLA actual (100% de 1–2★ en <48 h) y hacer una **campaña única de backfill** de las 48 reseñas negativas de 2023–2024. Es barato y mejora la primera impresión del perfil.

### 5.7 Reservas: problema resuelto, no prioridad
- **37 menciones, rating 2,95, −1,57★, 48,65% negativas** en el acumulado. Asusta, pero está concentrado en el pasado: **2023: 25 menciones, 2,68, 56,0% negativas**; 2024: 4/2,25; 2025: 4/3,50; **2026: 4/4,75, 0% negativas**.
- **Valor:** monitorear, no invertir. La fricción de reservas parece haber sido resuelta. Mantener confirmación y gestión de expectativa en horas pico.

### 5.8 Delivery: pequeño en volumen, severo en experiencia
- **11 menciones, rating 1,91, gap −2,61★, 81,82% negativas.** Persistente en los cuatro años (2023 5/1,60; 2024 2/2,00; 2025 3/2,67; 2026 1/1,00).
- Las quejas apuntan a **temperatura, packaging y faltantes**. En un producto que depende del punto de masa, el delivery castiga la propuesta.
- **Valor:** si el delivery no es estratégico, **acotarlo o rediseñarlo** (packaging térmico, validación de pedido, tiempos). Si se mantiene, tratarlo como un canal aparte con estándares propios.

### 5.9 Ocupación: la oportunidad está en el almuerzo
- Ocupación media **42,2%**. Pico **21:00 (66,7%)**. Día más cargado **sábado (59,9%)**.
- Por franja: **almuerzo 12–15 h ≈ 25,3%** vs. **cena 19–23 h ≈ 55,7%**. Las únicas horas bajo 25% son **12 h (16,0%) y 13 h (24,0%)**.
- Por día: Sábado 59,9, Viernes 47,6, Jueves 46,6, Miércoles 42,2, Domingo 40,7, Lunes 39,8. Martes no tiene datos de popular times.
- **Caveat de datos:** el lunes figura con horario de almuerzo pero 0% de ocupación, y el martes no devuelve datos. Hay que validarlo con el POS o con observación antes de sacar conclusiones.
- **Valor:** una propuesta de **almuerzo/after office (12–16 h)** —menú ejecutivo, porción individual, vermouth— llena capacidad sin canibalizar la cena. Medir con `occupancy.csv` antes/después y con reseñas por franja.

### 5.10 Competencia: top en rating, segundo en volumen
| Competidor | Reseñas | Rating |
|---|---:|---:|
| Siamo nel Forno | 4.301 | 4,4 |
| **ORNO Guatemala** | **1.897** | **4,5** |
| Tonno Soho | 1.707 | 4,2 |
| El Horno del Norte | 743 | 4,1 |
| ORNO Arenales (misma marca) | 566 | 4,6 |
| Orno Pizza Dot | 431 | 4,3 |

- ORNO tiene el **mejor rating del grupo** (4,5), empatado con su hermana Arenales (4,6), pero **no lidera volumen**: Siamo nel Forno lo duplica en reseñas.
- **Valor:** benchmark mensual de rating y temas. ORNO Arenales funciona como **laboratorio premium** de la marca; evitar canibalización y comparar precios/experiencia entre ambas.

### 5.11 Idioma y perfil: mercado local con margen turístico
- Español **92,73%** (1.759), inglés **3,85%** (73), otros **3,43%** (65; portugués 55, italiano 3, alemán 3).
- El perfil está al **100%**: precio, web, menú, horarios, descripción, teléfono, fotos, atributos, opciones de servicio, reservas y pagos. 1.031 imágenes, 46 atributos en 12 grupos.
- Único gap real: **categoría "Restaurante"** en lugar de **"Pizzería"**, y web en `http` (conviene `https`). Son correcciones de 5 minutos con impacto en búsqueda y conversión.
- **Valor:** contenido bilingüe selectivo (menú, reseñas destacadas, respuesta a turistas) en lugar de traducir todo. Palermo tiene flujo turístico suficiente para justificarlo.

### 5.12 Promotores silenciosos y sesgo del texto
- **79,49%** de las reseñas traen texto, un porcentaje alto para el sector. Aun así, **19,09% de las 5★ no tienen texto**.
- Consecuencia: el texto disponible sobrerrepresenta a detractores y a clientes muy involucrados. Los temas negativos pesan más de lo que pesan en la experiencia real.
- **Valor:** leer `themes.csv` como **dirección**, no como porcentaje exacto de la clientela; usar `mentions` para priorizar, no para extrapolar.

---

## 6. Temas: tabla completa

| Tema | Menciones | % texto | Rating | Gap | % positivas | % negativas |
|---|---:|---:|---:|---:|---:|---:|
| Servicio y atención | 869 | 57,63 | 4,63 | +0,11 | 91,37 | 5,52 |
| Comida y sabor | 747 | 49,54 | 4,49 | −0,03 | 87,68 | 8,17 |
| Ambiente y lugar | 550 | 36,47 | 4,44 | −0,08 | 85,82 | 8,55 |
| Fidelidad y recomendación | 220 | 14,59 | 4,65 | +0,13 | 92,27 | 5,91 |
| Precio y valor | 134 | 8,89 | 3,60 | −0,92 | 60,45 | 25,37 |
| Ocasión y grupos | 107 | 7,10 | 4,42 | −0,10 | 85,98 | 10,28 |
| Demora y espera | 58 | 3,85 | 2,59 | −1,93 | 32,76 | 51,72 |
| Música y ruido | 57 | 3,78 | 4,11 | −0,41 | 73,68 | 17,54 |
| Reservas | 37 | 2,45 | 2,95 | −1,57 | 40,54 | 48,65 |
| Logística y ubicación | 32 | 2,12 | 3,66 | −0,86 | 65,62 | 25,00 |
| Turismo | 11 | 0,73 | 4,82 | +0,30 | 90,91 | 0,00 |
| Delivery y para llevar | 11 | 0,73 | 1,91 | −2,61 | 9,09 | 81,82 |
| Pagos | 11 | 0,73 | 3,36 | −1,16 | 63,64 | 36,36 |

**Lectura rápida:** los tres temas masivos (servicio, comida, ambiente) están sanos y por encima de 4,4. Los problemas están en la **cola**: precio, espera, reservas, delivery y pagos. Esa cola es barata de atacar y muy visible en reseñas.

---

## 7. Productos: tabla completa

| Producto | Menciones | % texto | Rating | Gap | % positivas | % negativas |
|---|---:|---:|---:|---:|---:|---:|
| Pizza | 537 | 35,61 | 4,32 | −0,20 | 81,38 | 10,06 |
| Pizza Detroit | 104 | 6,90 | 4,28 | −0,24 | 76,92 | 8,65 |
| Cócteles y tragos | 93 | 6,17 | 4,39 | −0,13 | 82,80 | 6,45 |
| Empanadas | 89 | 5,90 | 4,11 | −0,41 | 71,91 | 11,24 |
| Pizza napolitana | 64 | 4,24 | 4,17 | −0,35 | 73,44 | 7,81 |
| Postres | 54 | 3,58 | 4,30 | −0,22 | 83,33 | 11,11 |
| Música | 54 | 3,58 | 4,19 | −0,33 | 75,93 | 14,81 |
| **Mora** | 51 | 3,38 | **4,96** | +0,44 | 100,00 | 0,00 |
| Fainá | 44 | 2,92 | 4,18 | −0,34 | 84,09 | 13,64 |
| Carne / parrilla | 41 | 2,72 | 3,88 | −0,64 | 68,29 | 17,07 |
| Reserva | 33 | 2,19 | 2,97 | −1,55 | 42,42 | 51,52 |
| Margarita | 32 | 2,12 | 4,16 | −0,36 | 75,00 | 12,50 |
| Pasta | 32 | 2,12 | 4,41 | −0,11 | 87,50 | 9,38 |
| Vino | 30 | 1,99 | 3,77 | −0,75 | 63,33 | 20,00 |
| Milanesa | 29 | 1,92 | 3,86 | −0,66 | 65,52 | 10,34 |
| **Pera** | 24 | 1,59 | **4,67** | +0,15 | 87,50 | 4,17 |
| Cumpleaños / celebración | 24 | 1,59 | 4,38 | −0,14 | 83,33 | 12,50 |
| Terraza | 23 | 1,53 | 4,30 | −0,22 | 78,26 | 8,70 |
| Cerveza | 20 | 1,33 | 3,55 | −0,97 | 60,00 | 30,00 |
| **Bingo** | 20 | 1,33 | **4,55** | +0,03 | 90,00 | 10,00 |
| **Stracciatella** | 18 | 1,19 | **4,56** | +0,04 | 88,89 | 0,00 |
| Niños / familia | 13 | 0,86 | 4,85 | +0,33 | 100,00 | 0,00 |
| Pizza porteña | 12 | 0,80 | 4,00 | −0,52 | 75,00 | 25,00 |
| Vermouth | 8 | 0,53 | 4,25 | −0,27 | 62,50 | 0,00 |
| Delivery | 8 | 0,53 | 2,12 | −2,40 | 12,50 | 75,00 |
| Café | 5 | 0,33 | 3,20 | −1,32 | 60,00 | 40,00 |

> Productos con menos de 10 menciones (Pistacho, Carpaccio, Turista) no se incluyen para evitar conclusiones sobre muestras demasiado chicas.

**Etiquetas de Google (top 10):** `oriana gonzález marzoli` (72), `pizza estilo detroit` (70), `faina` (41), `pizza napolitana` (38), `mora` (27), `peras` (24), `arquitectura` (20), `bingo` (16), `vermouth` (14), `stracciatella` (10).

La coincidencia entre etiquetas de Google y productos héroe es la mejor noticia del análisis: **lo que Google asocia a ORNO es exactamente lo que los clientes elogian**. La arquitectura (20 menciones) es un activo de ambiente que conviene mostrar más.

---

## 8. Cómo está armado el análisis (6 tablas, 100% determinista)

| Tabla | Grano | Para qué sirve |
|---|---|---|
| `restaurants.csv` | 1 fila por restaurante | Todos los KPIs de negocio (84 columnas) |
| `reviews.csv` | 1 fila por reseña | Filtros, verbatims y agregados ad hoc |
| `monthly_trend.csv` | restaurante × mes | Evolución y estacionalidad |
| `themes.csv` | restaurante × dimensión × etiqueta | Temas, productos y etiquetas Google |
| `occupancy.csv` | restaurante × día × hora | Operación y franjas |
| `competitors.csv` | restaurante × competidor | Benchmark |

Todo se calcula con **pandas, reglas y expresiones regulares**. El sentimiento es un proxy por estrellas; los temas y productos son coincidencia de palabras clave. No hay IA ni modelos de lenguaje en ninguna etapa.

---

## 9. Ideas de análisis priorizadas

### Quick wins (con los datos actuales, 1–2 semanas)
1. **Auditoría de precio/porción**: usar `themes.csv` + `reviews.csv` para listar las quejas de precio de 2026 y cruzar con la carta. Definir qué se comunica y cómo.
2. **Backfill de respuestas**: responder las **48 reseñas de 1–2★ de 2023–2024** que quedaron sin respuesta. Sube la cobertura de 1–2★ a 94,57%.
3. **SLA de espera**: medir tiempos por franja (21–22 h) y definir estándar de comunicación al cliente.
4. **Corregir categoría y web**: pasar de "Restaurante" a "Pizzería" y de `http` a `https`.
5. **Destacar productos héroe**: Mora, Pera/Detroit de peras, Stracciatella, Bingo y Vermouth en carta, menú de Google y guion de salón.
6. **Activar almuerzo**: propuesta 12–16 h (menú ejecutivo, porción individual, vermouth) y medir con `occupancy.csv`.

### Medio plazo (requiere integrar más datos)
7. **Integración con POS/reservas**: ticket promedio, margen y ventas por franja/plato. Es donde está el ROI real.
8. **Alertas automáticas**: caída de rating mensual, pico de 1–2★, subida de un tema negativo, caída de `pct_with_reply`.
9. **Segmentación**: Local Guides, turistas, familias, parejas y after office; rating y ticket por segmento.
10. **Benchmark competitivo continuo**: scraping mensual y comparación de rating/temas con Siamo nel Forno, Tonno y ORNO Arenales.
11. **Atribución de campañas**: efecto de promociones en volumen de reseñas, rating y ocupación.
12. **Análisis de respuesta por autor**: ¿responder a un detractor recupera su siguiente reseña?

### Avanzado
13. **Análisis causal de la respuesta del dueño**: comparar la evolución de quienes recibieron respuesta personalizada vs. plantilla.
14. **Predicción de riesgo de reseña negativa** por franja/producto/servicio.
15. **Modelo de expansión**: puntuar ubicaciones por demanda, competencia, turismo y rating esperado.
16. **Precio y elasticidad percibida**: cruzar menciones de precio, ticket y ventas para optimizar precios y porciones.

---

## 10. KPIs recomendados

**Satisfacción**
- Rating histórico y rating de la muestra (aquí coinciden: 4,5 vs. 4,52).
- NPS proxy: % 4–5★ − % 1–2★ (81,71).
- % reseñas 1–3★ y evolución mensual.
- Subratings: Comida 4,55, Servicio 4,66, Ambiente 4,63 (cobertura 87,14%).

**Marca y demanda**
- Velocidad de reseñas (1,32/día; 39,6/mes).
- % reseñas con texto (79,49%) y con foto (15,87%).
- % Local Guides (48,55%) y "promotores silenciosos" (% 5★ sin texto: 19,09%).

**Operación y servicio**
- % de reseñas respondidas (69,79% global; 91,48% en 2026).
- Cobertura de respuesta a 1–2★ (57,36%; 87,50% en 2026).
- % de respuestas personalizadas (84,59% con nombre).
- Tiempo de respuesta (cuando se capture la fecha).
- Ocupación por franja: almuerzo vs. cena.

**Producto y valor**
- Menciones y rating por producto/tema.
- % de menciones de precio y rating asociado (8,89%; 3,60).
- Temas negativos emergentes (espera, delivery, pagos).

**Perfil y conversión**
- Completitud del perfil de Google (100%).
- Categoría correcta (Pizzería) y web en `https`.
- Rating y volumen vs. competidores.

---

## 11. Modelo de datos

Las 6 tablas de `data/processed/` son la capa de consumo. El modelo subyacente sigue siendo:

- `restaurants` (dimensión enriquecida): identidad + perfil + KPIs agregados.
- `reviews` (hecho): una fila por reseña, con temas/productos y respuesta.
- `monthly_trend` (agregado): restaurante × mes.
- `themes` (puente en formato largo): restaurante × dimensión × etiqueta.
- `occupancy` (hecho): restaurante × día × hora (solo horarios de apertura).
- `competitors` (dimensión): restaurante × competidor.
- `fact_sales` (futuro): fecha, franja, plato, unidades, ingresos, margen.

---

## 12. Plan de acción 30/60/90 días

**Primeros 30 días**
1. **Precio/porción**: auditar las quejas de 2026 y ajustar comunicación de tamaños y formato en carta y menú de Google.
2. **Backfill de respuestas**: responder las 48 reseñas de 1–2★ de 2023–2024 con nombre y detalle.
3. **Categoría y web**: corregir "Restaurante" → "Pizzería" y `http` → `https`.
4. **Espera en hora pico**: medir tiempos en 21–22 h y definir estándar de comunicación.
5. **Productos héroe**: destacar Mora, Pera, Stracciatella, Bingo y Vermouth en carta y guion de salón.

**60 días**
6. **Almuerzo/after office**: lanzar propuesta 12–16 h y medir ocupación antes/después.
7. **Consistencia de pizza**: estandarizar punto de cocción y temperatura de salida por estilo (Detroit, napolitana, margarita, porteña).
8. **Delivery**: decidir si se acota o se rediseña (packaging térmico, validación de pedido, tiempos).
9. **Benchmark mensual**: Siamo nel Forno, Tonno Soho y ORNO Arenales.

**90 días**
10. **Integrar POS/reservas** para medir impacto en ventas, ticket y margen por franja/plato.
11. **Activar alertas automáticas** sobre `monthly_trend` y `themes`.
12. **Evaluar resultados**: rating, NPS proxy, % de quejas de precio, cobertura de respuesta, ocupación por franja y ventas.

---

## 13. Cómo mejorar la base de datos

- Mantener la extracción completa: hoy ya se captura el **100% del historial** (1.897 reseñas).
- Guardar **snapshots** (el pipeline acumula un raw por día y sobrescribe el mismo día): así se mide evolución real de rating, temas y competencia.
- Capturar **fecha de respuesta** del dueño (si Apify la expone en otro campo o vía otra fuente).
- Ampliar `competitors` para evitar registros con 0 reseñas y agregar competidores de la zona.
- Integrar **POS/reservas/delivery** para cuantificar el impacto económico.
- Validar la ocupación de **martes** y del **almuerzo del lunes**, que Google no devuelve.
- Estandarizar el nombre del restaurante (slug) y el `review_id` como claves.

---

## 14. Conclusión

ORNO ya demostró que puede operar al nivel de un 4,6–4,7: lo hizo en 2025 y lo sostiene en 2026. El desafío no es "mejorar la experiencia base", sino **defender el rating frente al crecimiento**:

1. **Precio/valor** es el único tema masivo que rompe el 4,0 y el que más creció en volumen de queja.
2. **La espera en hora pico** es el dolor operativo con peor gap (−1,93★) y se deterioró en 2026.
3. **La pizza necesita consistencia**, no reinvención: la marca ya tiene productos héroe (Mora, Pera, Stracciatella, Bingo) y un equipo que los clientes nombran.
4. **El almuerzo es la palanca de capacidad**: 25% de ocupación contra 56% en la cena.
5. **La reputación ya está gestionada**: el foco debe pasar de "responder más" a "responder mejor" y a operar la experiencia que genera las reseñas.

El mayor salto de valor no viene de más gráficos, sino de **cruzar reseñas con ventas/reservas** y de **medir la evolución mes a mes** en lugar de mirar una foto fija.
