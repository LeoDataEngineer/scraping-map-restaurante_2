"""
Dashboard de inteligencia de negocio para restaurantes.

Consume las 6 tablas generadas por `src/etl/transform.py` en `data/processed/`:
    - restaurants.csv     (una fila por restaurante, todos los KPIs)
    - reviews.csv         (una fila por reseña)
    - monthly_trend.csv   (evolución mensual)
    - themes.csv          (temas, productos y etiquetas de Google)
    - occupancy.csv       (ocupación por día y hora)
    - competitors.csv     (benchmark competitivo)

No usa IA ni servicios externos: todos los KPIs y alertas son deterministas.

Ejecutar:
    streamlit run app.py
"""

from pathlib import Path

import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# Configuración general
# ============================================================
# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

st.set_page_config(
    page_title="Inteligencia de Negocio · Restaurantes",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ACCENT = "#2563EB"
COLORS = ["#2563EB", "#F97316", "#10B981", "#8B5CF6", "#EF4444", "#0EA5E9", "#F59E0B", "#14B8A6"]
SENTIMENT_COLORS = {"Positivo": "#10B981", "Neutro": "#F59E0B", "Negativo": "#EF4444"}
GAP_COLORS = {"Por debajo de la media": "#EF4444", "Por encima de la media": "#10B981"}
OCCUPANCY_COLORS = {"Valle (<25%)": "#94A3B8", "Normal": "#60A5FA", "Pico (≥70%)": "#EF4444"}
PRIORITY_ICONS = {"Alta": "🔴 Alta", "Media": "🟠 Media", "Baja": "🟢 Baja"}

TABLE_FILES = [
    "restaurants.csv",
    "reviews.csv",
    "monthly_trend.csv",
    "themes.csv",
    "occupancy.csv",
    "competitors.csv",
]

COLUMN_LABELS = {
    "generated_at": "Generado",
    "restaurant_name": "Restaurante",
    "place_id": "Place ID",
    "category": "Categoría",
    "address": "Dirección",
    "city": "Ciudad",
    "state": "Estado",
    "price_range": "Rango de precio",
    "website": "Web",
    "phone": "Teléfono",
    "raw_file": "Archivo raw",
    "total_score_historical": "Rating histórico",
    "reviews_count_historical": "Reseñas históricas",
    "historical_5star_pct": "% 5★ histórico",
    "historical_4star_pct": "% 4★ histórico",
    "historical_3star_pct": "% 3★ histórico",
    "historical_1_2star_pct": "% 1–2★ histórico",
    "nps_proxy_historical": "NPS proxy histórico",
    "reviews_sample": "Reseñas analizadas",
    "sample_oldest_date": "Reseña más antigua",
    "sample_newest_date": "Reseña más reciente",
    "days_span": "Días cubiertos",
    "reviews_per_day": "Reseñas/día",
    "reviews_per_month": "Reseñas/mes",
    "recent_avg_rating": "Rating reciente",
    "recent_5star_pct": "% 5★ reciente",
    "recent_4star_pct": "% 4★ reciente",
    "recent_3star_pct": "% 3★ reciente",
    "recent_1_2star_pct": "% 1–2★ reciente",
    "nps_proxy_recent": "NPS proxy reciente",
    "rating_delta_recent_vs_historical": "Δ rating reciente vs histórico",
    "pct_with_text": "% con texto",
    "pct_5star_without_text": "% 5★ sin texto",
    "pct_4_5star_without_text": "% 4–5★ sin texto",
    "pct_with_photo": "% con foto",
    "avg_photos_per_review": "Fotos por reseña",
    "pct_local_guide": "% Local Guides",
    "median_reviewer_reviews": "Mediana reseñas del autor",
    "pct_with_detailed_rating": "% con rating detallado",
    "avg_food_rating": "Comida (prom.)",
    "avg_service_rating": "Servicio (prom.)",
    "avg_ambience_rating": "Ambiente (prom.)",
    "owner_response_rate": "% respuesta del dueño",
    "owner_response_rate_1_2star": "% respuesta a 1–2★",
    "owner_response_rate_1_3star": "% respuesta a 1–3★",
    "replied": "Respondidas",
    "reviews_1_2star": "Reseñas 1–2★",
    "replied_1_2star": "Respondidas 1–2★",
    "reviews_1_3star": "Reseñas 1–3★",
    "replied_1_3star": "Respondidas 1–3★",
    "generic_replies": "Respuestas genéricas",
    "generic_reply_pct": "% respuestas genéricas",
    "repeated_replies": "Respuestas repetidas",
    "repeated_reply_pct": "% respuestas repetidas",
    "named_replies": "Respuestas con nombre",
    "named_reply_pct": "% respuestas con nombre",
    "avg_reply_length": "Largo medio respuesta",
    "pct_spanish": "% español",
    "pct_english": "% inglés",
    "pct_other_language": "% otro idioma",
    "profile_score": "Score de perfil",
    "missing_profile_fields": "Campos faltantes",
    "has_price": "Precio",
    "has_website": "Web",
    "has_menu": "Menú",
    "has_hours": "Horarios",
    "has_description": "Descripción",
    "has_phone": "Teléfono",
    "has_photos": "Fotos",
    "has_attributes": "Atributos",
    "has_service_options": "Opciones de servicio",
    "has_reservations": "Reservas",
    "has_payments": "Pagos",
    "additional_info_groups": "Grupos de atributos",
    "additional_attributes": "Atributos totales",
    "images_count": "Imágenes",
    "peak_hour": "Hora pico",
    "peak_hour_avg_occupancy_pct": "Ocupación en pico %",
    "busiest_day": "Día más ocupado",
    "busiest_day_avg_occupancy_pct": "Ocupación del día top %",
    "dead_hours_lt25": "Horas valle (<25%)",
    "avg_occupancy_pct": "Ocupación media %",
    "pct_with_review_id": "% con review ID",
    "pct_with_language": "% con idioma",
    "year_month": "Mes",
    "is_partial_month": "Mes parcial",
    "reviews": "Reseñas",
    "avg_rating": "Rating prom.",
    "pct_1_3star": "% 1–3★",
    "pct_4_5star": "% 4–5★",
    "pct_with_reply": "% con respuesta",
    "avg_text_length": "Largo medio texto",
    "dimension": "Dimensión",
    "label": "Etiqueta",
    "mentions": "Menciones",
    "pct_of_text_reviews": "% de reseñas con texto",
    "rating_gap_vs_restaurant": "Diferencia vs media",
    "pct_positive": "% positivas",
    "pct_negative": "% negativas",
    "rank": "Ranking",
    "sample_rating": "Rating del ejemplo",
    "sample_date": "Fecha del ejemplo",
    "sample_verbatim": "Verbatim de ejemplo",
    "day": "Día",
    "hour": "Hora",
    "occupancy_pct": "Ocupación %",
    "competitor_name": "Competidor",
    "competitor_reviews": "Reseñas del competidor",
    "competitor_rating": "Rating del competidor",
    "stars": "Estrellas",
    "source": "Fuente",
    "pct": "%",
    "count": "Cantidad",
    "sentiment": "Sentimiento",
    "rating": "Estrellas",
    "author": "Autor",
    "publish_date": "Fecha",
    "publish_time": "Fecha/hora",
    "year_month": "Mes",
    "language": "Idioma",
    "review_text": "Texto",
    "text_length": "Largo del texto",
    "has_text": "Con texto",
    "likes_count": "Likes",
    "photos_count": "Fotos",
    "is_local_guide": "Local Guide",
    "reviewer_reviews": "Reseñas del autor",
    "owner_replied": "Respondida",
    "owner_reply_text": "Respuesta del dueño",
    "food_rating": "Comida",
    "service_rating": "Servicio",
    "ambience_rating": "Ambiente",
    "topics": "Temas",
    "products": "Productos",
    "reply_text": "Respuesta",
    "pct_of_replies": "% de respuestas",
    "prioridad": "Prioridad",
    "palanca": "Palanca",
    "accion": "Acción recomendada",
    "evidencia": "Evidencia",
}

DAY_ORDER = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
STAR_ORDER = ["5★", "4★", "3★", "1–2★"]
MONTH_ABBR = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


# ============================================================
# Carga y utilidades
# ============================================================
@st.cache_data(show_spinner=False)
def load_tables(directory: str, signature: int) -> dict:
    """Carga las 6 tablas. `signature` invalida la caché al regenerarlas."""
    base = Path(directory)
    tables = {}
    for file_name in TABLE_FILES:
        path = base / file_name
        if not path.exists():
            tables[file_name] = pd.DataFrame()
            continue
        try:
            tables[file_name] = pd.read_csv(path)
        except (pd.errors.EmptyDataError, OSError):
            tables[file_name] = pd.DataFrame()
    return tables


def data_signature(directory: Path) -> int:
    files = list(directory.glob("*.csv"))
    return int(max((f.stat().st_mtime for f in files), default=0))


def number(value):
    """Convierte un valor a float de forma segura."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_pct(value, decimals=1):
    v = number(value)
    return "—" if v is None else f"{v:,.{decimals}f}%"


def fmt_dec(value, decimals=2):
    v = number(value)
    return "—" if v is None else f"{v:,.{decimals}f}"


def fmt_int(value):
    v = number(value)
    return "—" if v is None else f"{int(v):,}"


def style_fig(fig, height=360, show_legend=True):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(size=12),
        legend=(
            dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None)
            if show_legend
            else dict()
        ),
    )
    return fig


def show_table(df, pct_cols=(), num_cols=(), int_cols=(), drop=(), height=None):
    """Muestra una tabla con etiquetas en español y formato numérico."""
    if df is None or df.empty:
        st.info("No hay datos para los filtros seleccionados.")
        return

    data = df.drop(columns=[c for c in drop if c in df.columns]).copy()
    data = data.rename(columns={k: v for k, v in COLUMN_LABELS.items() if k in data.columns})

    config = {}
    for col in pct_cols:
        label = COLUMN_LABELS.get(col, col)
        if label in data.columns:
            config[label] = st.column_config.NumberColumn(label, format="%.1f")
    for col in num_cols:
        label = COLUMN_LABELS.get(col, col)
        if label in data.columns:
            config[label] = st.column_config.NumberColumn(label, format="%.2f")
    for col in int_cols:
        label = COLUMN_LABELS.get(col, col)
        if label in data.columns:
            config[label] = st.column_config.NumberColumn(label, format="%d")

    kwargs = {}
    if height is not None:
        kwargs["height"] = height

    st.dataframe(
        data,
        column_config=config,
        hide_index=True,
        use_container_width=True,
        **kwargs,
    )


def download_csv(df, label, file_name, key):
    if df is None or df.empty:
        return
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=file_name,
        mime="text/csv",
        key=key,
    )


def occupancy_state(value):
    v = number(value)
    if v is None:
        return "Sin dato"
    if v < 25:
        return "Valle (<25%)"
    if v >= 70:
        return "Pico (≥70%)"
    return "Normal"


def stars_text(value):
    v = number(value)
    if v is None:
        return "—"
    filled = int(round(v))
    return "★" * filled + "☆" * (5 - filled)


def month_label(value):
    """Convierte '2026-11' en 'nov 2026' para ejes en español."""
    try:
        dt = pd.to_datetime(str(value) + "-01")
        return f"{MONTH_ABBR[dt.month - 1]} {dt.year}"
    except (ValueError, TypeError):
        return str(value)


def render_plain_text(text, muted=False):
    """Muestra texto de usuario sin interpretar Markdown ni LaTeX.

    Streamlit trata `$...$` como fórmula matemática: una reseña con precios
    ("30$ ... 75$") se renderiza como LaTeX, pierde los espacios y se rompe
    carácter por línea. Aquí se escapa el HTML y se fuerza el ajuste de línea.
    """
    value = html.escape(str(text), quote=False)
    style = (
        "white-space: pre-wrap; overflow-wrap: break-word; word-break: normal; "
        "line-height: 1.55;"
    )
    if muted:
        style += " font-size: 0.875rem; color: #6b7280;"
    st.markdown(f"<div style='{style}'>{value}</div>", unsafe_allow_html=True)


# ============================================================
# Métricas derivadas de las reseñas (sin volver al raw)
# ============================================================
def reviews_by_rating(reviews: pd.DataFrame) -> pd.DataFrame:
    if reviews is None or reviews.empty:
        return pd.DataFrame()

    data = reviews.copy()
    data["rating"] = pd.to_numeric(data["rating"], errors="coerce")
    total = len(data)
    rows = []

    for stars in range(1, 6):
        subset = data[data["rating"] == stars]
        n = len(subset)
        rows.append({
            "stars": stars,
            "reviews": n,
            "pct_of_reviews": round(n / total * 100, 1) if total else None,
            "pct_with_text": round(subset["has_text"].mean() * 100, 1) if n else None,
            "pct_with_reply": round(subset["owner_replied"].mean() * 100, 1) if n else None,
            "pct_with_photo": round((subset["photos_count"] > 0).mean() * 100, 1) if n else None,
            "avg_text_length": round(subset["text_length"].mean(), 1) if n else None,
            "avg_likes": round(subset["likes_count"].mean(), 2) if n else None,
            "avg_food_rating": round(subset["food_rating"].mean(), 2) if n and subset["food_rating"].notna().any() else None,
            "avg_service_rating": round(subset["service_rating"].mean(), 2) if n and subset["service_rating"].notna().any() else None,
            "avg_ambience_rating": round(subset["ambience_rating"].mean(), 2) if n and subset["ambience_rating"].notna().any() else None,
        })

    return pd.DataFrame(rows)


def sentiment_summary(reviews: pd.DataFrame) -> pd.DataFrame:
    if reviews is None or reviews.empty:
        return pd.DataFrame()
    total = len(reviews)
    rows = []
    for sentiment in ["Positivo", "Neutro", "Negativo"]:
        count = int((reviews["sentiment"] == sentiment).sum())
        rows.append({
            "sentiment": sentiment,
            "reviews": count,
            "pct": round(count / total * 100, 1) if total else None,
        })
    return pd.DataFrame(rows)


def repeated_templates(reviews: pd.DataFrame, min_count: int = 2) -> pd.DataFrame:
    if reviews is None or reviews.empty:
        return pd.DataFrame()

    replied = reviews[
        reviews["owner_replied"].fillna(False) & reviews["owner_reply_text"].notna()
    ]
    if replied.empty:
        return pd.DataFrame()

    texts = replied["owner_reply_text"].astype(str).str.strip()
    templates = (
        texts[texts != ""]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "reply_text", "owner_reply_text": "reply_text", "count": "count"})
    )
    templates = templates[templates["count"] >= min_count].sort_values("count", ascending=False)
    templates["pct_of_replies"] = (templates["count"] / len(replied) * 100).round(1)
    return templates.reset_index(drop=True)


def occupancy_aggregates(occupancy: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if occupancy is None or occupancy.empty:
        return pd.DataFrame(), pd.DataFrame()

    data = occupancy.dropna(subset=["hour", "occupancy_pct"]).copy()
    # Excluir horas cerradas (Google las reporta con 0) para no subestimar
    # la ocupación real ni marcar como "valle" franjas que no abren.
    data = data[data["occupancy_pct"] > 0].copy()
    data["hour"] = data["hour"].astype(int)

    by_hour = (
        data.groupby("hour")["occupancy_pct"]
        .agg(avg_occupancy_pct="mean", max_occupancy_pct="max", min_occupancy_pct="min")
        .reset_index()
    )
    by_hour["avg_occupancy_pct"] = by_hour["avg_occupancy_pct"].round(1)
    by_hour["max_occupancy_pct"] = by_hour["max_occupancy_pct"].round(1)
    by_hour["min_occupancy_pct"] = by_hour["min_occupancy_pct"].round(1)

    by_day = (
        data.groupby("day")["occupancy_pct"]
        .agg(avg_occupancy_pct="mean", max_occupancy_pct="max")
        .reset_index()
    )
    by_day["avg_occupancy_pct"] = by_day["avg_occupancy_pct"].round(1)
    by_day["max_occupancy_pct"] = by_day["max_occupancy_pct"].round(1)
    by_day["day"] = pd.Categorical(by_day["day"], categories=DAY_ORDER, ordered=True)
    by_day = by_day.sort_values("day")

    return by_hour, by_day


def distribution_frame(row) -> pd.DataFrame:
    """Distribución histórica de estrellas del perfil de Google."""
    values = {
        "5★": row.get("historical_5star_pct"),
        "4★": row.get("historical_4star_pct"),
        "3★": row.get("historical_3star_pct"),
        "1–2★": row.get("historical_1_2star_pct"),
    }
    rows = []
    for stars, value in values.items():
        pct_value = number(value)
        if pct_value is not None:
            rows.append({"stars": stars, "pct": pct_value})
    return pd.DataFrame(rows)


# ============================================================
# Alertas y plan de acción (reglas deterministas)
# ============================================================
def build_insights(row, themes: pd.DataFrame) -> list[dict]:
    name = row["restaurant_name"]
    insights = []

    rating = number(row.get("recent_avg_rating"))
    delta = number(row.get("rating_delta_recent_vs_historical"))
    response_rate = number(row.get("owner_response_rate"))
    response_12 = number(row.get("owner_response_rate_1_2star"))
    pct_12 = number(row.get("recent_1_2star_pct"))
    generic = number(row.get("generic_reply_pct"))
    repeated = number(row.get("repeated_reply_pct"))
    named = number(row.get("named_reply_pct"))
    silent_5star = number(row.get("pct_5star_without_text"))
    profile = number(row.get("profile_score"))
    peak_hour = number(row.get("peak_hour"))
    peak_pct = number(row.get("peak_hour_avg_occupancy_pct"))
    dead = str(row.get("dead_hours_lt25") or "").strip()

    def add(level, title, detail):
        insights.append({"level": level, "title": title, "detail": detail, "restaurant": name})

    if rating is not None and rating >= 4.5:
        add("success", "Satisfacción sólida",
            f"Rating reciente de {rating:.2f}★. La experiencia gusta y hay base para crecer sin corregir la propuesta de valor.")

    if delta is not None and delta <= -0.05:
        add("warning", "Rating reciente a la baja",
            f"El rating reciente está {abs(delta):.2f}★ por debajo del histórico. Revisar qué cambió en servicio, precio o producto.")
    elif delta is not None and delta >= 0.05:
        add("success", "Mejora vs histórico",
            f"El rating reciente supera el histórico en {delta:+.2f}★. La operación actual está funcionando mejor que el promedio acumulado.")

    if response_rate is not None and response_rate < 90:
        add("warning", "Cobertura de respuesta mejorable",
            f"Se responde el {response_rate:.1f}% de las reseñas. Cada reseña sin respuesta es una señal de abandono para el cliente y para el algoritmo.")

    if response_12 is not None and pct_12 is not None and pct_12 > 0 and response_12 < 80:
        add("error", "Detractores sin respuesta",
            f"Solo se responde el {response_12:.1f}% de las reseñas de 1–2★. Es la conversación más importante: ahí se recupera reputación.")

    if generic is not None and generic >= 50:
        add("warning", "Respuestas poco personalizadas",
            f"El {generic:.1f}% de las respuestas son plantillas de agradecimiento. No mencionan el problema ni el nombre, y no invitan a volver.")

    if repeated is not None and repeated >= 30:
        add("warning", "Plantillas repetidas",
            f"El {repeated:.1f}% de las respuestas repite exactamente el mismo texto. El cliente lo nota y reduce la credibilidad de la marca.")

    if named is not None and named < 40:
        add("info", "Oportunidad: personalizar con el nombre",
            f"Solo el {named:.1f}% de las respuestas menciona el nombre del autor. Personalizar es una acción de bajo costo y alto impacto.")

    if silent_5star is not None and silent_5star >= 50:
        add("info", "Promotores silenciosos",
            f"El {silent_5star:.1f}% de las reseñas de 5★ no tienen texto. Pedir reseña con texto o foto en el momento de la experiencia genera más señal.")

    if profile is not None and profile < 70:
        missing = row.get("missing_profile_fields")
        missing_txt = f" Faltan: {missing}." if isinstance(missing, str) and missing else ""
        add("warning", "Perfil de Google incompleto",
            f"El perfil está al {profile:.1f}% de completitud.{missing_txt} Completarlo mejora la conversión desde Maps.")

    if themes is not None and not themes.empty:
        topic_data = themes[themes["dimension"] == "Tema"].copy()
        topic_data = topic_data[pd.to_numeric(topic_data["mentions"], errors="coerce") >= 5]

        for _, topic_row in topic_data.iterrows():
            gap = number(topic_row.get("rating_gap_vs_restaurant"))
            avg = number(topic_row.get("avg_rating"))
            mentions = number(topic_row.get("mentions"))
            if gap is not None and gap <= -0.5:
                rating_txt = f"{avg:.2f}★" if avg is not None else "sin rating"
                add("error", f"Tema crítico: {topic_row['label']}",
                    f"{int(mentions or 0)} menciones con rating promedio de {rating_txt} ({gap:+.2f} vs la media). Es un dolor concreto y accionable.")

        best = topic_data.dropna(subset=["rating_gap_vs_restaurant"]).sort_values(
            ["rating_gap_vs_restaurant", "mentions"], ascending=False
        )
        if not best.empty:
            top = best.iloc[0]
            gap = number(top.get("rating_gap_vs_restaurant"))
            if gap is not None and gap >= 0.4:
                avg = number(top.get("avg_rating"))
                rating_txt = f"{avg:.2f}★" if avg is not None else "sin rating"
                add("success", f"Tema promotor: {top['label']}",
                    f"{int(number(top.get('mentions')) or 0)} menciones con rating {rating_txt} ({gap:+.2f} vs la media). Es una palanca de marketing.")

    if dead:
        add("info", "Capacidad ociosa identificada",
            f"Horas valle (<25% de ocupación): {dead}. Son espacio para promociones de almuerzo o after office sin canibalizar la cena.")

    if peak_hour is not None and peak_pct is not None:
        add("warning", "Riesgo operativo en hora pico",
            f"El pico es a las {int(peak_hour)}:00 con {peak_pct:.1f}% de ocupación media. Reforzar dotación y separar cobro/café para evitar demoras.")

    priority = {"error": 0, "warning": 1, "success": 2, "info": 3}
    return sorted(insights, key=lambda item: priority.get(item["level"], 9))


def build_actions(row, themes: pd.DataFrame) -> pd.DataFrame:
    name = row["restaurant_name"]
    actions = []

    response_12 = number(row.get("owner_response_rate_1_2star"))
    pct_12 = number(row.get("recent_1_2star_pct"))
    generic = number(row.get("generic_reply_pct"))
    repeated = number(row.get("repeated_reply_pct"))
    named = number(row.get("named_reply_pct"))
    silent = number(row.get("pct_5star_without_text"))
    profile = number(row.get("profile_score"))
    missing = row.get("missing_profile_fields")
    dead = str(row.get("dead_hours_lt25") or "").strip()
    peak_hour = number(row.get("peak_hour"))

    if response_12 is not None and pct_12 is not None and pct_12 > 0 and response_12 < 80:
        actions.append({
            "restaurant_name": name,
            "prioridad": "Alta",
            "palanca": "Recuperación de detractores",
            "accion": "Responder el 100% de las reseñas de 1–2★ en menos de 48 h, con disculpa específica, acción concreta y seguimiento.",
            "evidencia": f"Respuesta actual a 1–2★: {response_12:.1f}%",
        })

    if (generic is not None and generic >= 50) or (repeated is not None and repeated >= 30):
        actions.append({
            "restaurant_name": name,
            "prioridad": "Alta",
            "palanca": "Calidad de respuesta",
            "accion": "Sustituir plantillas por respuestas personalizadas: nombre, detalle de la experiencia y próxima visita. Crear 3 variantes por tipo de reseña.",
            "evidencia": f"Genéricas: {fmt_pct(generic)} · Repetidas: {fmt_pct(repeated)} · Con nombre: {fmt_pct(named)}",
        })

    if themes is not None and not themes.empty:
        topic_data = themes[themes["dimension"] == "Tema"].copy()
        worst = topic_data[
            (pd.to_numeric(topic_data["mentions"], errors="coerce") >= 5)
            & (pd.to_numeric(topic_data["rating_gap_vs_restaurant"], errors="coerce") <= -0.5)
        ].sort_values("rating_gap_vs_restaurant")
        if not worst.empty:
            top = worst.iloc[0]
            actions.append({
                "restaurant_name": name,
                "prioridad": "Alta",
                "palanca": f"Resolver dolor: {top['label']}",
                "accion": f"Revisar proceso, comunicación y expectativas asociadas a {str(top['label']).lower()}. Definir un responsable y medir el rating del tema en 30 días.",
                "evidencia": f"{int(number(top['mentions']) or 0)} menciones · rating {fmt_dec(top['avg_rating'], 2)}★ ({number(top['rating_gap_vs_restaurant']):+.2f} vs media)",
            })

    if profile is not None and profile < 70:
        missing_txt = missing if isinstance(missing, str) and missing else "campos clave"
        actions.append({
            "restaurant_name": name,
            "prioridad": "Media",
            "palanca": "Perfil de Google",
            "accion": f"Completar el perfil: {missing_txt}. Incluir precio, menú, web, opciones de servicio, reservas y pagos.",
            "evidencia": f"Completitud actual: {profile:.1f}%",
        })

    if silent is not None and silent >= 50:
        actions.append({
            "restaurant_name": name,
            "prioridad": "Media",
            "palanca": "Generación de reseñas con texto",
            "accion": "Activar QR/follow-up post-visita para pedir reseña con texto o foto, con incentivo no monetario y foco en clientes satisfechos.",
            "evidencia": f"{silent:.1f}% de las 5★ no tienen texto",
        })

    if dead:
        actions.append({
            "restaurant_name": name,
            "prioridad": "Media",
            "palanca": "Activar horas valle",
            "accion": f"Lanzar promoción de almuerzo/after office en las horas {dead} y medir ocupación y ticket por franja.",
            "evidencia": "Ocupación media <25% en esas horas",
        })

    if peak_hour is not None:
        actions.append({
            "restaurant_name": name,
            "prioridad": "Media",
            "palanca": "Dotación en hora pico",
            "accion": f"Reforzar personal entre {int(peak_hour) - 2}:00 y {int(peak_hour) + 2}:00, separar cobro de café y habilitar pago digital.",
            "evidencia": f"Pico a las {int(peak_hour)}:00 con {fmt_pct(row.get('peak_hour_avg_occupancy_pct'))} de ocupación media",
        })

    actions_df = pd.DataFrame(actions)
    if actions_df.empty:
        return actions_df
    actions_df["prioridad_orden"] = actions_df["prioridad"].map({"Alta": 0, "Media": 1, "Baja": 2})
    actions_df = actions_df.sort_values(["prioridad_orden", "palanca"]).drop(columns=["prioridad_orden"])
    return actions_df.reset_index(drop=True)


# ============================================================
# Pestaña 1: Resumen
# ============================================================
def render_summary(row, restaurants, monthly, themes):
    st.subheader("Resumen ejecutivo")
    st.caption(
        "Rating, demanda, respuesta del dueño y salud del perfil de Google. "
        "Los deltas comparan la muestra reciente contra el histórico del perfil."
    )

    delta = number(row.get("rating_delta_recent_vs_historical"))
    delta_label = f"{delta:+.2f} vs histórico" if delta is not None else None

    cols = st.columns(6)
    cols[0].metric("Rating reciente", fmt_dec(row.get("recent_avg_rating"), 2), delta=delta_label)
    cols[1].metric("NPS proxy", fmt_pct(row.get("nps_proxy_recent"), 0))
    cols[2].metric("Reseñas / mes", fmt_dec(row.get("reviews_per_month"), 1))
    cols[3].metric("Reseñas analizadas", fmt_int(row.get("reviews_sample")))
    cols[4].metric("Respuesta dueño", fmt_pct(row.get("owner_response_rate")))
    cols[5].metric("Respuesta 1–2★", fmt_pct(row.get("owner_response_rate_1_2star")))

    st.caption(
        f"{row.get('category') or 'Sin categoría'} · {row.get('city') or 'Sin ciudad'} · "
        f"{fmt_int(row.get('reviews_count_historical'))} reseñas históricas · "
        f"Perfil de Google al {fmt_pct(row.get('profile_score'))}"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Evolución del rating**")
        if monthly.empty:
            st.info("No hay datos mensuales.")
        else:
            data = monthly.copy()
            data = data.sort_values("year_month")
            data = data.tail(24)
            data["is_partial_month"] = data["is_partial_month"].astype(bool)
            data["periodo"] = data["year_month"].apply(month_label)

            fig = px.line(
                data,
                x="periodo",
                y="avg_rating",
                markers=True,
                color_discrete_sequence=[ACCENT],
                hover_data={
                    "year_month": True,
                    "reviews": True,
                    "pct_1_3star": ":.1f",
                    "pct_with_reply": ":.1f",
                    "is_partial_month": False,
                },
                labels={"periodo": "Mes", "avg_rating": "Rating promedio"},
            )
            fig.update_xaxes(type="category")
            historical = number(row.get("total_score_historical"))
            if historical is not None:
                fig.add_hline(
                    y=historical,
                    line_dash="dot",
                    line_color="#94A3B8",
                    annotation_text=f"Histórico {historical:.2f}",
                    annotation_position="bottom right",
                )
            fig.update_yaxes(dtick=0.2)
            st.plotly_chart(style_fig(fig, height=340, show_legend=False), use_container_width=True)
            st.caption("Últimos 24 meses. El mes en curso es parcial: no comparar su volumen con meses completos.")

    with col2:
        st.markdown("**Distribución histórica de estrellas**")
        dist = distribution_frame(row)
        if dist.empty:
            st.info("No hay datos de distribución histórica.")
        else:
            fig = px.bar(
                dist,
                x="stars",
                y="pct",
                color="stars",
                text_auto=".0f",
                category_orders={"stars": STAR_ORDER},
                labels={"stars": "Estrellas", "pct": "% de reseñas"},
            )
            fig.update_yaxes(range=[0, 105])
            fig.update_layout(showlegend=False)
            st.plotly_chart(style_fig(fig, height=340, show_legend=False), use_container_width=True)
            st.caption("Distribución del perfil de Google: todas las reseñas históricas.")

    with st.expander("Comparar con otros restaurantes"):
        comparison = restaurants.copy()
        comparison["_seleccionado"] = comparison["restaurant_name"] == row["restaurant_name"]
        comparison = comparison.sort_values("_seleccionado", ascending=False).drop(columns="_seleccionado")
        columns = [
            "restaurant_name", "total_score_historical", "recent_avg_rating",
            "rating_delta_recent_vs_historical", "reviews_per_month", "nps_proxy_recent",
            "owner_response_rate", "owner_response_rate_1_2star", "profile_score",
        ]
        columns = [column for column in columns if column in comparison.columns]
        show_table(
            comparison[columns],
            pct_cols=["nps_proxy_recent", "owner_response_rate", "owner_response_rate_1_2star", "profile_score"],
            num_cols=["total_score_historical", "recent_avg_rating", "rating_delta_recent_vs_historical", "reviews_per_month"],
        )

    st.divider()
    st.markdown("### Alertas y oportunidades")
    insights = build_insights(row, themes)
    if not insights:
        st.info("Sin alertas relevantes con los datos actuales.")
        return

    def show_insight(insight):
        message = f"**{insight['title']}**  \n{insight['detail']}"
        level = insight["level"]
        if level == "error":
            st.error(message)
        elif level == "warning":
            st.warning(message)
        elif level == "success":
            st.success(message)
        else:
            st.info(message)

    for insight in insights[:4]:
        show_insight(insight)

    if len(insights) > 4:
        with st.expander(f"Ver {len(insights) - 4} alertas más"):
            for insight in insights[4:]:
                show_insight(insight)


# ============================================================
# Pestaña 2: Satisfacción y reseñas
# ============================================================
def render_reviews(row, reviews):
    st.subheader("Satisfacción y reseñas")
    st.caption("Comportamiento por estrella, sentimiento y explorador de reseñas con verbatims.")

    if reviews.empty:
        st.info("No hay reseñas para este restaurante.")
        return

    data = reviews.copy()
    data["publish_dt"] = pd.to_datetime(data["publish_time"], errors="coerce", utc=True)
    data["publish_date_obj"] = data["publish_dt"].dt.date
    data["rating"] = pd.to_numeric(data["rating"], errors="coerce")
    data["has_text"] = data["has_text"].fillna(False).astype(bool)
    data["owner_replied"] = data["owner_replied"].fillna(False).astype(bool)

    by_rating = reviews_by_rating(data)
    sentiment = sentiment_summary(data)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Comportamiento por estrella**")
        chart_df = by_rating.melt(
            id_vars="stars",
            value_vars=["pct_with_text", "pct_with_reply"],
            var_name="metrica",
            value_name="pct",
        ).dropna(subset=["pct"])
        chart_df["metrica"] = chart_df["metrica"].map({
            "pct_with_text": "% con texto",
            "pct_with_reply": "% con respuesta",
        })
        fig = px.bar(
            chart_df,
            x="stars",
            y="pct",
            color="metrica",
            barmode="group",
            text_auto=".0f",
            color_discrete_sequence=["#94A3B8", ACCENT],
            labels={"stars": "Estrellas", "pct": "% de reseñas", "metrica": ""},
        )
        fig.update_xaxes(dtick=1)
        fig.update_yaxes(range=[0, 105])
        st.plotly_chart(style_fig(fig, height=320), use_container_width=True)
        st.caption("Los clientes insatisfechos suelen escribir más: el texto disponible no es una muestra neutral.")

    with col2:
        st.markdown("**Sentimiento (proxy por estrellas)**")
        fig = px.pie(
            sentiment,
            names="sentiment",
            values="reviews",
            hole=0.55,
            color="sentiment",
            color_discrete_map=SENTIMENT_COLORS,
            category_orders={"sentiment": ["Positivo", "Neutro", "Negativo"]},
        )
        fig.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(style_fig(fig, height=320), use_container_width=True)
        st.caption("Positivo = 4–5★ · Neutro = 3★ · Negativo = 1–2★. Proxy determinista, no análisis de lenguaje.")

    with st.expander("Ver métricas por estrella"):
        show_table(
            by_rating,
            pct_cols=["pct_of_reviews", "pct_with_text", "pct_with_reply", "pct_with_photo"],
            num_cols=["avg_text_length", "avg_likes", "avg_food_rating", "avg_service_rating", "avg_ambience_rating"],
            int_cols=["stars", "reviews"],
        )

    st.divider()
    st.markdown("### Explorador de reseñas")

    valid_dates = data["publish_date_obj"].dropna()
    min_date = valid_dates.min() if not valid_dates.empty else None
    max_date = valid_dates.max() if not valid_dates.empty else None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if min_date is not None and max_date is not None:
            date_range = st.date_input(
                "Rango de fechas",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="review_date_range",
            )
        else:
            date_range = None
    with col2:
        rating_range = st.slider("Estrellas", 1, 5, (1, 5), key="review_rating_range")
    with col3:
        search = st.text_input("Buscar en el texto", placeholder="ej. demora, precio, pizza…", key="review_search")
    with col4:
        sort_option = st.selectbox(
            "Ordenar por",
            ["Más recientes", "Rating más bajo", "Rating más alto", "Textos más largos"],
            key="review_sort",
        )

    topic_options = sorted({
        item.strip()
        for value in data["topics"].fillna("").astype(str)
        for item in value.split(";")
        if item.strip()
    })
    product_options = sorted({
        item.strip()
        for value in data["products"].fillna("").astype(str)
        for item in value.split(";")
        if item.strip()
    })

    col5, col6, col7 = st.columns([2, 2, 1])
    with col5:
        selected_topics = st.multiselect("Temas", topic_options, key="review_topics")
    with col6:
        selected_products = st.multiselect("Productos", product_options, key="review_products")
    with col7:
        only_text = st.checkbox("Solo con texto", value=False, key="review_only_text")
        only_unanswered = st.checkbox("Solo sin respuesta", value=False, key="review_only_unanswered")

    mask = data["rating"].between(rating_range[0], rating_range[1], inclusive="both")

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        mask &= data["publish_date_obj"].between(start_date, end_date)
    elif isinstance(date_range, tuple) and len(date_range) == 1:
        mask &= data["publish_date_obj"] == date_range[0]

    if search:
        mask &= data["review_text"].fillna("").str.contains(search, case=False, regex=False)
    if selected_topics:
        mask &= data["topics"].fillna("").apply(
            lambda value: any(topic in [x.strip() for x in value.split(";")] for topic in selected_topics)
        )
    if selected_products:
        mask &= data["products"].fillna("").apply(
            lambda value: any(product in [x.strip() for x in value.split(";")] for product in selected_products)
        )
    if only_text:
        mask &= data["has_text"]
    if only_unanswered:
        mask &= ~data["owner_replied"]

    view = data[mask].copy()
    sort_map = {
        "Más recientes": ("publish_dt", False),
        "Rating más bajo": ("rating", True),
        "Rating más alto": ("rating", False),
        "Textos más largos": ("text_length", False),
    }
    sort_column, ascending = sort_map[sort_option]
    view = view.sort_values(sort_column, ascending=ascending, na_position="last")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Reseñas filtradas", f"{len(view):,}")
    kpi2.metric("Rating promedio", fmt_dec(view["rating"].mean(), 2))
    kpi3.metric("% con texto", fmt_pct(view["has_text"].mean() * 100 if len(view) else None))
    kpi4.metric("% con respuesta", fmt_pct(view["owner_replied"].mean() * 100 if len(view) else None))

    if view.empty:
        st.info("Ninguna reseña cumple los filtros.")
        return

    table_columns = [
        "publish_date", "author", "rating", "sentiment", "topics",
        "products", "text_length", "owner_replied",
    ]
    st.dataframe(
        view[table_columns],
        hide_index=True,
        use_container_width=True,
        column_config={
            "publish_date": "Fecha",
            "author": "Autor",
            "rating": st.column_config.NumberColumn("Estrellas", format="%d"),
            "sentiment": "Sentimiento",
            "topics": "Temas",
            "products": "Productos",
            "text_length": st.column_config.NumberColumn("Largo del texto", format="%d"),
            "owner_replied": "Respondida",
        },
        height=300,
    )
    download_csv(view, "Descargar reseñas filtradas", "reviews_filtered.csv", "dl_reviews")

    st.markdown(f"**Reseñas destacadas** (mostrando {min(6, len(view))} de {len(view):,})")
    for _, review in view.head(6).iterrows():
        with st.container(border=True):
            head = st.columns([4, 1, 1.2])
            head[0].markdown(f"**{review.get('author') or 'Anónimo'}**")
            head[1].markdown(stars_text(review.get("rating")))
            head[2].caption(str(review.get("publish_date") or "")[:10])

            if review.get("has_text") and isinstance(review.get("review_text"), str):
                render_plain_text(review["review_text"])
            else:
                st.caption("_Sin texto_")

            meta_parts = []
            if isinstance(review.get("topics"), str) and review["topics"]:
                meta_parts.append(f"Temas: {review['topics']}")
            if isinstance(review.get("products"), str) and review["products"]:
                meta_parts.append(f"Productos: {review['products']}")
            if meta_parts:
                st.caption(" · ".join(meta_parts))

            if bool(review.get("owner_replied")):
                with st.expander("Ver respuesta del dueño"):
                    render_plain_text(review.get("owner_reply_text") or "")
            else:
                st.caption("⚠️ Sin respuesta del dueño")


# ============================================================
# Pestaña 3: Temas y respuestas
# ============================================================
def render_voice_and_responses(row, themes, reviews):
    st.subheader("Temas y respuestas")
    st.caption(
        "Qué mencionan los clientes, qué temas castigan la satisfacción y cómo responde el dueño. "
        "La diferencia vs. la media indica si un tema eleva o reduce el rating."
    )

    if themes.empty:
        st.info("No hay temas detectados para este restaurante.")
    else:
        st.markdown("**Temas y productos: frecuencia vs. satisfacción**")
        chart_data = themes[
            themes["dimension"].isin(["Tema", "Producto"])
            & (pd.to_numeric(themes["mentions"], errors="coerce") > 0)
            & themes["avg_rating"].notna()
            & themes["pct_of_text_reviews"].notna()
        ].copy()

        if chart_data.empty:
            st.info("No hay menciones suficientes en la muestra actual.")
        else:
            fig = px.scatter(
                chart_data,
                x="pct_of_text_reviews",
                y="avg_rating",
                size="mentions",
                color="dimension",
                hover_name="label",
                hover_data={
                    "mentions": True,
                    "avg_rating": ":.2f",
                    "rating_gap_vs_restaurant": ":.2f",
                    "pct_positive": ":.1f",
                },
                color_discrete_map={"Tema": ACCENT, "Producto": "#F97316"},
                size_max=40,
                labels={
                    "pct_of_text_reviews": "% de reseñas con texto",
                    "avg_rating": "Rating promedio",
                    "dimension": "",
                },
            )
            fig.update_yaxes(range=[1, 5.2])
            st.plotly_chart(style_fig(fig, height=360), use_container_width=True)

        st.markdown("**Detalle de temas y productos**")
        dimension = st.selectbox(
            "Dimensión", ["Todos", "Tema", "Producto"], key="theme_dimension"
        )
        table_data = themes[themes["dimension"].isin(["Tema", "Producto"])].copy()
        if dimension != "Todos":
            table_data = table_data[table_data["dimension"] == dimension]
        table_data = table_data[table_data["mentions"].fillna(0) > 0].sort_values(
            ["mentions", "rating_gap_vs_restaurant"], ascending=[False, True]
        )
        show_table(
            table_data.drop(columns=["sample_verbatim"], errors="ignore"),
            pct_cols=["pct_of_text_reviews", "pct_positive", "pct_negative"],
            num_cols=["avg_rating", "rating_gap_vs_restaurant"],
            int_cols=["mentions", "sample_rating"],
            height=320,
        )

        examples = table_data.dropna(subset=["sample_verbatim"]).head(3)
        if not examples.empty:
            with st.expander("Ver ejemplos de reseñas por tema"):
                for _, example in examples.iterrows():
                    st.markdown(
                        f"**{example['label']}** · {stars_text(example.get('sample_rating'))} · "
                        f"{example.get('sample_date') or 'sin fecha'}"
                    )
                    render_plain_text(f"“{example['sample_verbatim']}”", muted=True)

        tags = themes[themes["dimension"] == "Etiqueta Google"].sort_values("rank")
        if not tags.empty:
            with st.expander("Ver etiquetas que Google destaca"):
                show_table(
                    tags[["label", "mentions", "rank"]],
                    int_cols=["mentions", "rank"],
                )

    st.divider()
    st.markdown("### Respuesta del dueño")

    cols = st.columns(5)
    cols[0].metric("Tasa de respuesta", fmt_pct(row.get("owner_response_rate")))
    cols[1].metric("Respuesta 1–2★", fmt_pct(row.get("owner_response_rate_1_2star")))
    cols[2].metric("Genéricas", fmt_pct(row.get("generic_reply_pct")))
    cols[3].metric("Repetidas", fmt_pct(row.get("repeated_reply_pct")))
    cols[4].metric("Con nombre", fmt_pct(row.get("named_reply_pct")))

    response_metrics = pd.DataFrame([
        {"metrica": "Tasa de respuesta", "pct": number(row.get("owner_response_rate")), "grupo": "Cobertura"},
        {"metrica": "Respuesta 1–2★", "pct": number(row.get("owner_response_rate_1_2star")), "grupo": "Cobertura"},
        {"metrica": "Respuesta 1–3★", "pct": number(row.get("owner_response_rate_1_3star")), "grupo": "Cobertura"},
        {"metrica": "Con nombre", "pct": number(row.get("named_reply_pct")), "grupo": "Personalización"},
        {"metrica": "Genéricas", "pct": number(row.get("generic_reply_pct")), "grupo": "Personalización"},
        {"metrica": "Repetidas", "pct": number(row.get("repeated_reply_pct")), "grupo": "Personalización"},
    ]).dropna(subset=["pct"])

    if not response_metrics.empty:
        fig = px.bar(
            response_metrics.sort_values("pct"),
            x="pct",
            y="metrica",
            orientation="h",
            color="grupo",
            text_auto=".0f",
            color_discrete_map={"Cobertura": ACCENT, "Personalización": "#F97316"},
            labels={"pct": "%", "metrica": "", "grupo": ""},
        )
        fig.update_xaxes(range=[0, 105])
        st.plotly_chart(style_fig(fig, height=320), use_container_width=True)

    templates = repeated_templates(reviews)
    st.markdown("**Respuestas más repetidas**")
    if templates.empty:
        st.info("No hay respuestas repetidas (o no hay respuestas registradas).")
    else:
        preview = templates.head(10).copy()
        preview["reply_text"] = preview["reply_text"].astype(str).str.slice(0, 100).str.strip() + "…"
        show_table(
            preview,
            pct_cols=["pct_of_replies"],
            int_cols=["count"],
            height=300,
        )
        with st.expander("Ver todas las respuestas repetidas"):
            show_table(templates, pct_cols=["pct_of_replies"], int_cols=["count"])


# ============================================================
# Pestaña 4: Operación y perfil
# ============================================================
def render_operations(row, occupancy, competitors):
    st.subheader("Operación y perfil")
    st.caption(
        "Ocupación estimada por Google (popular times), completitud del perfil y benchmark competitivo. "
        "La ocupación no es un conteo real de ventas."
    )

    st.markdown("### Ocupación por día y hora")
    by_hour, by_day = occupancy_aggregates(occupancy)

    if occupancy.empty:
        st.info("Este restaurante no expone datos de ocupación (popular times) en Google.")
    else:
        cols = st.columns(5)
        cols[0].metric("Hora pico", f"{int(number(row.get('peak_hour')) or 0)}:00")
        cols[1].metric("Ocupación en pico", fmt_pct(row.get("peak_hour_avg_occupancy_pct")))
        cols[2].metric("Día más ocupado", row.get("busiest_day") or "—")
        cols[3].metric("Ocupación media", fmt_pct(row.get("avg_occupancy_pct")))
        cols[4].metric("Horas valle", row.get("dead_hours_lt25") or "—")

        pivot = occupancy.pivot_table(
            index="day",
            columns="hour",
            values="occupancy_pct",
            aggfunc="mean",
        ).reindex([day for day in DAY_ORDER if day in occupancy["day"].unique()])

        fig = px.imshow(
            pivot,
            text_auto=".0f",
            aspect="auto",
            color_continuous_scale="YlOrRd",
            zmin=0,
            zmax=100,
            labels={"x": "Hora", "y": "Día", "color": "Ocupación %"},
        )
        st.plotly_chart(style_fig(fig, height=340, show_legend=False), use_container_width=True)

        st.markdown("**Ocupación media por hora**")
        hour_plot = by_hour.copy()
        hour_plot["estado"] = hour_plot["avg_occupancy_pct"].apply(occupancy_state)
        fig = px.bar(
            hour_plot,
            x="hour",
            y="avg_occupancy_pct",
            color="estado",
            text_auto=".0f",
            color_discrete_map=OCCUPANCY_COLORS,
            labels={"hour": "Hora", "avg_occupancy_pct": "Ocupación media %", "estado": ""},
        )
        fig.update_xaxes(dtick=1)
        fig.update_yaxes(range=[0, 105])
        st.plotly_chart(style_fig(fig, height=320), use_container_width=True)

        dead = str(row.get("dead_hours_lt25") or "").strip()
        if dead:
            st.info(
                f"**Capacidad ociosa:** las horas {dead} están por debajo del 25% de ocupación. "
                "Una promoción de almuerzo o after office puede llenar esas franjas sin competir con la cena."
            )

        with st.expander("Ver tabla de ocupación por hora"):
            show_table(
                by_hour,
                pct_cols=["avg_occupancy_pct", "max_occupancy_pct", "min_occupancy_pct"],
                int_cols=["hour"],
            )

    st.divider()
    st.markdown("### Perfil de Google")
    profile_score = number(row.get("profile_score"))
    st.metric("Completitud del perfil", fmt_pct(profile_score))

    fields = [
        ("has_price", "Precio"), ("has_website", "Web"), ("has_menu", "Menú"),
        ("has_hours", "Horarios"), ("has_description", "Descripción"), ("has_phone", "Teléfono"),
        ("has_photos", "Fotos"), ("has_attributes", "Atributos"),
        ("has_service_options", "Opciones de servicio"), ("has_reservations", "Reservas"),
        ("has_payments", "Pagos"),
    ]
    matrix_rows = []
    for field, label in fields:
        value = row.get(field)
        matrix_rows.append({
            "Campo": label,
            "Estado": "✅" if pd.notna(value) and bool(value) else "❌",
        })
    st.dataframe(pd.DataFrame(matrix_rows), hide_index=True, use_container_width=True)

    missing = row.get("missing_profile_fields")
    if isinstance(missing, str) and missing.strip():
        st.warning(f"Campos faltantes: {missing}")
    else:
        st.success("El perfil tiene todos los campos evaluados.")

    st.divider()
    st.markdown("### Competencia")
    if competitors.empty:
        st.info("No hay competidores identificados para este restaurante.")
        return

    competitors = competitors.copy()
    competitors["competitor_reviews"] = pd.to_numeric(competitors["competitor_reviews"], errors="coerce")
    competitors["competitor_rating"] = pd.to_numeric(competitors["competitor_rating"], errors="coerce")
    competitors = competitors.dropna(subset=["competitor_reviews", "competitor_rating"])

    own = pd.DataFrame([{
        "competitor_name": row["restaurant_name"],
        "competitor_reviews": row.get("reviews_count_historical"),
        "competitor_rating": row.get("total_score_historical"),
        "tipo": "Nosotros",
    }])
    plot_df = pd.concat(
        [
            competitors[["competitor_name", "competitor_reviews", "competitor_rating"]].assign(tipo="Competidor"),
            own,
        ],
        ignore_index=True,
    )
    plot_df["competitor_reviews"] = pd.to_numeric(plot_df["competitor_reviews"], errors="coerce")
    plot_df["competitor_rating"] = pd.to_numeric(plot_df["competitor_rating"], errors="coerce")
    plot_df = plot_df.dropna(subset=["competitor_reviews", "competitor_rating"])

    if not plot_df.empty:
        fig = px.scatter(
            plot_df,
            x="competitor_reviews",
            y="competitor_rating",
            size="competitor_reviews",
            color="tipo",
            text="competitor_name",
            hover_name="competitor_name",
            size_max=45,
            color_discrete_map={"Nosotros": ACCENT, "Competidor": "#94A3B8"},
            labels={"competitor_reviews": "Reseñas históricas", "competitor_rating": "Rating", "tipo": ""},
        )
        fig.update_traces(textposition="top center")
        fig.update_yaxes(range=[3.5, 5.1])
        st.plotly_chart(style_fig(fig, height=400), use_container_width=True)

    show_table(
        competitors,
        num_cols=["competitor_rating"],
        int_cols=["competitor_reviews"],
    )


# ============================================================
# Pestaña 5: Plan de acción
# ============================================================
def render_plan(row, themes):
    st.subheader("Plan de acción priorizado")
    st.caption(
        "Reglas deterministas sobre los KPIs: cada acción está conectada con una métrica y una evidencia. "
        "No es una recomendación generada por IA."
    )

    actions = build_actions(row, themes)
    if actions.empty:
        st.info("No se detectaron acciones prioritarias con los datos actuales.")
        return

    display = actions.copy()
    display["prioridad"] = display["prioridad"].map(PRIORITY_ICONS).fillna(display["prioridad"])
    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        column_config={
            "restaurant_name": "Restaurante",
            "prioridad": "Prioridad",
            "palanca": "Palanca",
            "accion": st.column_config.TextColumn("Acción recomendada", width="large"),
            "evidencia": st.column_config.TextColumn("Evidencia", width="medium"),
        },
    )
    download_csv(actions, "Descargar plan de acción", "plan_de_accion.csv", "dl_actions")

    st.divider()
    st.markdown("**Foco de esta semana**")
    for _, action in actions.head(3).iterrows():
        message = f"**{action['palanca']}** ({action['prioridad']})  \n{action['accion']}  \nEvidencia: {action['evidencia']}"
        if action["prioridad"] == "Alta":
            st.error(message)
        elif action["prioridad"] == "Media":
            st.warning(message)
        else:
            st.info(message)

    st.divider()
    st.markdown("**Rutina sugerida**")
    st.markdown(
        "- **Semanal:** revisar reseñas nuevas, responder 1–3★ en <48 h y actualizar el plan de acción.\n"
        "- **Mensual:** comparar rating, volumen, temas y competencia; ajustar dotación y promociones por franja.\n"
        "- **Trimestral:** revisar perfil de Google, precios/porciones y mezcla de productos."
    )


# ============================================================
# App
# ============================================================
def main():
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
        [data-testid="stMetricValue"] {font-size: 1.55rem;}
        [data-testid="stMetricLabel"] {font-size: 0.8rem;}
        h1, h2, h3 {letter-spacing: -0.02em;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    signature = data_signature(PROCESSED_DIR)
    tables = load_tables(str(PROCESSED_DIR), signature)

    restaurants = tables["restaurants.csv"]
    reviews_all = tables["reviews.csv"]
    monthly_all = tables["monthly_trend.csv"]
    themes_all = tables["themes.csv"]
    occupancy_all = tables["occupancy.csv"]
    competitors_all = tables["competitors.csv"]

    with st.sidebar:
        st.title("🍽️ Analytics")
        st.caption("Inteligencia de reseñas · Google Maps")

        if restaurants.empty:
            st.error("No se encontraron tablas. Ejecuta `python src/etl/transform.py` primero.")
            st.stop()

        names = restaurants["restaurant_name"].tolist()
        selected = st.selectbox("Restaurante", names, index=0, key="restaurant_select")

        row = restaurants[restaurants["restaurant_name"] == selected].iloc[0]
        reviews = reviews_all[reviews_all["restaurant_name"] == selected].copy()
        monthly = monthly_all[monthly_all["restaurant_name"] == selected].copy()
        themes = themes_all[themes_all["restaurant_name"] == selected].copy()
        occupancy = occupancy_all[occupancy_all["restaurant_name"] == selected].copy()
        competitors = competitors_all[competitors_all["restaurant_name"] == selected].copy()

        generated = row.get("generated_at")
        st.caption(f"**Datos actualizados:** {generated or '—'}")
        st.caption(
            f"6 tablas · {len(restaurants):,} restaurantes · "
            f"{len(reviews_all):,} reseñas · {len(themes_all):,} temas/productos"
        )

        if st.button("🔄 Recargar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.divider()
        with st.expander("Calidad de datos", expanded=False):
            st.markdown(
                f"**Cobertura**  \n"
                f"Reseñas analizadas: {fmt_int(row.get('reviews_sample'))}  \n"
                f"Reseñas históricas: {fmt_int(row.get('reviews_count_historical'))}  \n"
                f"Periodo: {row.get('sample_oldest_date') or '—'} → {row.get('sample_newest_date') or '—'} "
                f"({fmt_int(row.get('days_span'))} días)  \n"
                f"Archivo fuente: `{row.get('raw_file') or '—'}`"
            )
            quality = pd.DataFrame([
                {"Indicador": "% con texto", "Valor": fmt_pct(row.get("pct_with_text"))},
                {"Indicador": "% con review ID", "Valor": fmt_pct(row.get("pct_with_review_id"))},
                {"Indicador": "% con rating detallado", "Valor": fmt_pct(row.get("pct_with_detailed_rating"))},
                {"Indicador": "% con idioma", "Valor": fmt_pct(row.get("pct_with_language"))},
                {"Indicador": "% con foto", "Valor": fmt_pct(row.get("pct_with_photo"))},
            ])
            st.dataframe(quality, hide_index=True, use_container_width=True)
            st.caption(
                "Muestra: reseñas más recientes que devuelve Apify, no el historial completo. "
                "Sentimiento = proxy por estrellas. Temas = palabras clave. "
                "Ocupación = estimación de Google, no ventas reales."
            )

        with st.expander("Descargar tablas", expanded=False):
            table = st.selectbox("Tabla", TABLE_FILES, key="download_table")
            table_df = tables.get(table, pd.DataFrame())
            if not table_df.empty:
                st.caption(f"{len(table_df):,} filas · {len(table_df.columns)} columnas")
                download_csv(table_df, f"Descargar {table}", table, "dl_any_table")

        with st.expander("Metodología", expanded=False):
            st.markdown(
                "Todos los indicadores se calculan con pandas y reglas deterministas "
                "(estrellas, palabras clave y expresiones regulares). "
                "No se envían datos a ningún modelo de IA.\n\n"
                "Fuente: reseñas y perfil público de Google Maps vía Apify."
            )

    st.title("Panel de inteligencia de negocio")
    st.caption(
        "Reseñas, satisfacción, operación y competencia en una sola vista. "
        "Análisis determinista, sin IA, listo para decidir."
    )

    tab_summary, tab_reviews, tab_voice, tab_operations, tab_plan = st.tabs([
        "📊 Resumen",
        "⭐ Satisfacción y reseñas",
        "💬 Temas y respuestas",
        "🕒 Operación y perfil",
        "🎯 Plan de acción",
    ])

    with tab_summary:
        render_summary(row, restaurants, monthly, themes)

    with tab_reviews:
        render_reviews(row, reviews)

    with tab_voice:
        render_voice_and_responses(row, themes, reviews)

    with tab_operations:
        render_operations(row, occupancy, competitors)

    with tab_plan:
        render_plan(row, themes)


if __name__ == "__main__":
    main()
