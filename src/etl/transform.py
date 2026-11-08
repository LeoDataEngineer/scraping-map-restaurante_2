"""
Genera tablas CSV de análisis de negocio a partir de los archivos raw de Apify.

IMPORTANTE: este script NO usa IA ni servicios externos. Todo el análisis es
determinista:
  - KPIs calculados con pandas.
  - Sentimiento por estrellas (4-5 positivo, 3 neutro, 1-2 negativo).
  - Temas y productos detectados con palabras clave / expresiones regulares.

Salidas: data/processed/*.csv (listas para consumir desde Streamlit).

Uso:
    python src/etl/transform.py

Se puede ejecutar cada vez que se agreguen restaurantes o reseñas nuevas:
los nombres de archivo son estables y se sobrescriben con los datos actuales.
"""

import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

# Evitar errores de codificación con emojis en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ==========================================
# Diccionarios de temas y productos (sin IA)
# ==========================================
TOPICS = {
    "Servicio y atención": r"\b(atencion|servicio|meser\w*|personal|camarer\w*|mozo\w*|trato|amable\w*|groser\w*|simpatic\w*)\b",
    "Demora y espera": r"\b(demora\w*|espera\w*|tard\w*|lento|lenta|horas? de espera)\b",
    "Precio y valor": r"\b(precio\w*|caro|caros|caras|costos\w*|barato\w*|cuenta|cobr\w*|presupuesto|economic\w*|valor)\b",
    "Comida y sabor": r"\b(sabor\w*|comida|delicios\w*|ric[oa]s?|exquisit\w*|plato\w*|porcion\w*|carta|menu\w*)\b",
    "Ambiente y lugar": r"\b(ambiente|lugar\w*|terraza\w*|parque|decoracion|vista\w*|acogedor\w*|bonit[oa]s?|lind[oa]s?|salon|clima|aire|arquitectura|disen\w*)\b",
    "Música y ruido": r"\b(musica|ruido|volumen)\b",
    "Logística y ubicación": r"\b(estacionamiento|parking|ubicacion|acceso|llegar|palermo)\b",
    "Reservas": r"\b(reserva\w*|turno\w*)\b",
    "Ocasión y grupos": r"\b(familia\w*|ninos?|cumplean\w*|aniversario|grupo\w*|amigos?|pareja\w*|celebra\w*|brunch|desayuno\w*|almuerzo\w*|cena\w*)\b",
    "Turismo": r"\b(turista\w*|vacacion\w*|viaje\w*|visit\w*)\b",
    "Fidelidad y recomendación": r"\b(volver|regresar|regresamos|recomend\w*|repetir|otra vez|siempre)\b",
    "Delivery y para llevar": r"\b(delivery|domicilio|para llevar|take ?away|pedidos? ya|rappi)\b",
    "Pagos": r"\b(pago\w*|tarjeta\w*|efectivo|nfc|propina\w*|transferencia\w*)\b",
}

PRODUCTS = {
    "Pizza": r"\b(pizza\w*)\b",
    "Pizza Detroit": r"\b(detroit)\b",
    "Pizza napolitana": r"\b(napolitan\w*)\b",
    "Pizza porteña": r"\b(porten\w*|fugazzeta\w*|muzzarella|mozzarella)\b",
    "Margarita": r"\b(margarita\w*|margherita)\b",
    "Fainá": r"\b(fain\w*)\b",
    "Empanadas": r"\b(empanada\w*)\b",
    "Milanesa": r"\b(milanesa\w*)\b",
    "Pasta": r"\b(pasta\w*|arancini|raviol\w*|noqui\w*)\b",
    "Postres": r"\b(postre\w*|torta\w*|tiramisu|dulce\w*|helado\w*)\b",
    "Mora": r"\b(mora\w*)\b",
    "Pera": r"\b(peras?)\b",
    "Stracciatella": r"\b(stracciatella)\b",
    "Pistacho": r"\b(pistach\w*)\b",
    "Carpaccio": r"\b(carpaccio)\b",
    "Cócteles y tragos": r"\b(coctel\w*|trago\w*|mojito|gin|aperol|negroni)\b",
    "Cerveza": r"\b(cerveza\w*|birra\w*)\b",
    "Vino": r"\b(vino\w*|malbec)\b",
    "Vermouth": r"\b(vermouth|vermu)\b",
    "Café": r"\b(cafe|cappuccino|capuchino|espresso|expreso|latte)\b",
    "Carne / parrilla": r"\b(carne\w*|parrilla\w*|bistec\w*|bife\w*|bondiola\w*|pulpo\w*|pescado\w*|salmon)\b",
    "Terraza": r"\b(terraza\w*)\b",
    "Música": r"\b(musica)\b",
    "Bingo": r"\b(bingo)\b",
    "Estacionamiento": r"\b(estacionamiento|parking)\b",
    "Reserva": r"\b(reserva\w*)\b",
    "Niños / familia": r"\b(ninos?|familia\w*)\b",
    "Cumpleaños / celebración": r"\b(cumplean\w*|aniversario|celebra\w*)\b",
    "Turista": r"\b(turista\w*|vacacion\w*)\b",
    "Delivery": r"\b(delivery|domicilio|para llevar)\b",
}

GRATITUDE_REPLY_PATTERNS = [
    r"gracias por su visita",
    r"gracias por visitarnos",
    r"gracias por tu visita",
    r"gracias por visitar",
]

DAY_MAP = {
    "Mo": "Lunes",
    "Tu": "Martes",
    "We": "Miércoles",
    "Th": "Jueves",
    "Fr": "Viernes",
    "Sa": "Sábado",
    "Su": "Domingo",
}

# ==========================================
# Salida consolidada: 6 tablas con esquema estable
# ==========================================
REVIEWS_COLUMNS = [
    "restaurant_name", "place_id", "review_id", "author", "rating", "sentiment",
    "publish_time", "publish_date", "year_month", "language", "review_text",
    "text_length", "has_text", "likes_count", "photos_count", "is_local_guide",
    "reviewer_reviews", "owner_replied", "owner_reply_text",
    "food_rating", "service_rating", "ambience_rating", "topics", "products",
]
RESTAURANTS_COLUMNS = [
    "generated_at",
    "restaurant_name", "place_id", "category", "address", "city", "state",
    "price_range", "website", "phone", "raw_file",
    "total_score_historical", "reviews_count_historical",
    "historical_5star_pct", "historical_4star_pct", "historical_3star_pct",
    "historical_1_2star_pct", "nps_proxy_historical",
    "reviews_sample", "sample_oldest_date", "sample_newest_date", "days_span",
    "reviews_per_day", "reviews_per_month",
    "recent_avg_rating", "recent_5star_pct", "recent_4star_pct",
    "recent_3star_pct", "recent_1_2star_pct", "nps_proxy_recent",
    "rating_delta_recent_vs_historical",
    "pct_with_text", "pct_5star_without_text", "pct_4_5star_without_text",
    "pct_with_photo", "avg_photos_per_review", "pct_local_guide",
    "median_reviewer_reviews", "pct_with_detailed_rating",
    "avg_food_rating", "avg_service_rating", "avg_ambience_rating",
    "owner_response_rate", "owner_response_rate_1_2star", "owner_response_rate_1_3star",
    "replied", "reviews_1_2star", "replied_1_2star",
    "reviews_1_3star", "replied_1_3star",
    "generic_replies", "generic_reply_pct",
    "repeated_replies", "repeated_reply_pct",
    "named_replies", "named_reply_pct", "avg_reply_length",
    "pct_spanish", "pct_english", "pct_other_language",
    "profile_score", "missing_profile_fields",
    "has_price", "has_website", "has_menu", "has_hours", "has_description",
    "has_phone", "has_photos", "has_attributes", "has_service_options",
    "has_reservations", "has_payments", "additional_info_groups",
    "additional_attributes", "images_count",
    "peak_hour", "peak_hour_avg_occupancy_pct", "busiest_day",
    "busiest_day_avg_occupancy_pct", "dead_hours_lt25", "avg_occupancy_pct",
    "pct_with_review_id", "pct_with_language",
]
MONTHLY_COLUMNS = [
    "restaurant_name", "year_month", "is_partial_month", "reviews", "avg_rating",
    "pct_1_3star", "pct_4_5star", "pct_with_text", "pct_with_reply",
    "avg_text_length", "pct_with_photo",
]
THEMES_COLUMNS = [
    "restaurant_name", "dimension", "label", "mentions",
    "pct_of_text_reviews", "avg_rating", "rating_gap_vs_restaurant",
    "pct_positive", "pct_negative", "rank",
    "sample_rating", "sample_date", "sample_verbatim",
]
OCCUPANCY_COLUMNS = ["restaurant_name", "day", "hour", "occupancy_pct"]
OCCUPANCY_SUMMARY_COLUMNS = [
    "restaurant_name", "peak_hour", "peak_hour_avg_occupancy_pct",
    "busiest_day", "busiest_day_avg_occupancy_pct",
    "dead_hours_lt25", "avg_occupancy_pct",
]
COMPETITOR_COLUMNS = [
    "restaurant_name", "competitor_name", "competitor_reviews", "competitor_rating",
]
PROFILE_COLUMNS = [
    "restaurant_name", "has_price", "has_website", "has_menu", "has_hours",
    "has_description", "has_phone", "has_photos", "has_attributes",
    "has_service_options", "has_reservations", "has_payments",
    "additional_info_groups", "additional_attributes", "images_count",
    "profile_score", "missing_profile_fields",
]


# ==========================================
# Utilidades
# ==========================================
def pct(numerator, denominator):
    """Porcentaje redondeado; None si el denominador es 0."""
    if not denominator:
        return None
    return round(numerator / denominator * 100, 2)


def safe_mean(series):
    """Promedio redondeado; None si no hay datos."""
    series = series.dropna()
    if series.empty:
        return None
    return round(float(series.mean()), 2)


def clean_text(text):
    """Quita HTML, decodifica entidades y normaliza espacios."""
    import html

    text = str(text or "")
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(text):
    """Minúsculas y sin acentos, para comparar palabras clave de forma robusta."""
    text = clean_text(text).lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip()


RAW_DATE_RE = re.compile(r"_apify_raw_data_(\d{4}-\d{2}-\d{2})$")


def raw_file_date(path):
    """Fecha de extracción codificada en el nombre: <slug>_apify_raw_data_<YYYY-MM-DD>.json."""
    match = RAW_DATE_RE.search(path.stem)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def raw_file_rank(path):
    """Ordena por fecha del nombre y, si empatan, por fecha de modificación.

    La fecha del nombre refleja cuándo se extrajo el dato; el mtime solo
    desempata. Así un archivo viejo copiado hoy no le gana a la extracción
    más reciente del restaurante.
    """
    date = raw_file_date(path)
    mtime = path.stat().st_mtime
    return (date is not None, date or datetime.min.date(), mtime)


def find_latest_raw_files():
    """Archivo raw más reciente por restaurante (deduplicado por place_id)."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    latest = {}
    for path in RAW_DIR.glob("*.json"):
        if "_apify_raw_data_" not in path.stem:
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        items = raw_data if isinstance(raw_data, list) else [raw_data]
        if not items:
            continue

        place_id = items[0].get("placeId")
        key = place_id or path.stem.split("_apify_raw_data_")[0]
        current = latest.get(key)
        if current is None or raw_file_rank(path) > raw_file_rank(current):
            latest[key] = path

    if not latest:
        raise FileNotFoundError(
            f"No se encontraron archivos raw en '{RAW_DIR}'. Ejecuta 'python src/etl/extract.py' primero."
        )

    selected = sorted(latest.values(), key=lambda p: p.name)
    print("\n📄 Archivo raw más reciente por restaurante:")
    for path in selected:
        date = raw_file_date(path)
        modified = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        label = date.isoformat() if date else "sin fecha en el nombre"
        print(f"   • {path.name}  (extracción: {label} · modificado: {modified})")

    return selected


def load_restaurants():
    """Carga todos los restaurantes desde los raw más recientes."""
    restaurants = []
    used_names = set()

    for path in find_latest_raw_files():
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        items = raw_data if isinstance(raw_data, list) else [raw_data]
        for item in items:
            name = clean_text(item.get("title")) or path.stem.split("_apify_raw_data_")[0]
            if name in used_names:
                name = f"{name} ({str(item.get('placeId'))[-4:]})"
            used_names.add(name)
            restaurants.append({"name": name, "meta": item, "raw_file": path.name})

    return restaurants


def reviews_to_frame(item):
    """Convierte las reseñas de un restaurante en un DataFrame limpio."""
    records = []
    for review in item.get("reviews") or []:
        detailed = review.get("reviewDetailedRating") or {}
        text = clean_text(review.get("text"))
        reply = clean_text(review.get("responseFromOwnerText"))
        records.append({
            "place_id": item.get("placeId"),
            "review_id": review.get("reviewId"),
            "author": clean_text(review.get("name")),
            "rating": review.get("stars"),
            "publish_time": review.get("publishedAtDate"),
            "language": (review.get("originalLanguage") or review.get("translatedLanguage") or "").lower(),
            "review_text": text,
            "text_length": len(text),
            "has_text": bool(text),
            "likes_count": review.get("likesCount") or 0,
            "photos_count": len(review.get("reviewImageUrls") or []),
            "is_local_guide": bool(review.get("isLocalGuide")),
            "reviewer_reviews": review.get("reviewerNumberOfReviews") or 0,
            "owner_replied": bool(reply),
            "owner_reply_text": reply,
            "food_rating": detailed.get("Comida"),
            "service_rating": detailed.get("Servicio"),
            "ambience_rating": detailed.get("Ambiente"),
        })

    df = pd.DataFrame(records)
    if df.empty:
        df = pd.DataFrame(columns=[
            "place_id", "review_id", "author", "rating", "publish_time", "language",
            "review_text", "text_length", "has_text", "likes_count", "photos_count",
            "is_local_guide", "reviewer_reviews", "owner_replied",
            "owner_reply_text", "food_rating", "service_rating", "ambience_rating",
        ])

    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["publish_dt"] = pd.to_datetime(df["publish_time"], errors="coerce", utc=True)
    df["publish_date"] = df["publish_dt"].dt.strftime("%Y-%m-%d")
    df["year_month"] = df["publish_dt"].dt.strftime("%Y-%m")

    df["text_norm"] = df["review_text"].apply(normalize_text)
    df["reply_norm"] = df["owner_reply_text"].apply(normalize_text)

    df["sentiment"] = df["rating"].apply(
        lambda r: "Positivo" if r >= 4 else ("Neutro" if r == 3 else ("Negativo" if pd.notna(r) else None))
    )

    return df


def match_topics(text_norm, dictionary):
    """Devuelve los nombres de temas/productos que aparecen en el texto."""
    matches = []
    for label, pattern in dictionary.items():
        if text_norm and re.search(pattern, text_norm):
            matches.append(label)
    return "; ".join(matches)


def generic_reply_mask(series):
    """Marca respuestas que solo agradecen la visita (plantilla genérica)."""
    pattern = "|".join(GRATITUDE_REPLY_PATTERNS)
    return series.str.contains(pattern, regex=True, na=False)


def repeated_reply_mask(series):
    """Marca respuestas cuyo texto exacto se repite 2 o más veces."""
    series = series.fillna("")
    counts = series.value_counts()
    repeated_texts = set(counts[counts >= 2].index) - {""}
    return series.isin(repeated_texts)


def mentions_name(row):
    """¿La respuesta menciona el primer nombre del autor?"""
    if not row["owner_replied"] or not row["author"]:
        return False
    first_name = normalize_text(row["author"]).split()[0] if normalize_text(row["author"]) else ""
    return len(first_name) >= 3 and first_name in row["reply_norm"]


def profile_info(meta):
    """Completitud del perfil de Google y campos faltantes."""
    additional = meta.get("additionalInfo") or {}
    n_attributes = sum(len(values) for values in additional.values() if isinstance(values, list))

    components = {
        "price": bool(meta.get("price")),
        "website": bool(meta.get("website")),
        "menu": bool(meta.get("menu")),
        "hours": bool(meta.get("openingHours")),
        "description": bool(meta.get("ownerDescription")),
        "phone": bool(meta.get("phone")),
        "photos": (meta.get("imagesCount") or 0) > 0,
        "attributes": len(additional) > 0,
        "service_options": "Opciones de servicio" in additional,
        "reservations": "Planificación" in additional,
        "payments": "Pagos" in additional,
    }

    labels = {
        "price": "precio",
        "website": "sitio web",
        "menu": "menú",
        "hours": "horarios",
        "description": "descripción",
        "phone": "teléfono",
        "photos": "fotos",
        "attributes": "atributos",
        "service_options": "opciones de servicio",
        "reservations": "reservas",
        "payments": "pagos",
    }

    missing = [labels[key] for key, value in components.items() if not value]
    score = round(sum(components.values()) / len(components) * 100, 1)

    return {
        "has_price": components["price"],
        "has_website": components["website"],
        "has_menu": components["menu"],
        "has_hours": components["hours"],
        "has_description": components["description"],
        "has_phone": components["phone"],
        "has_photos": components["photos"],
        "has_attributes": components["attributes"],
        "has_service_options": components["service_options"],
        "has_reservations": components["reservations"],
        "has_payments": components["payments"],
        "additional_info_groups": len(additional),
        "additional_attributes": n_attributes,
        "images_count": meta.get("imagesCount") or 0,
        "profile_score": score,
        "missing_profile_fields": ", ".join(missing) if missing else "",
    }


def build_restaurant_metrics(restaurant):
    """Calcula KPIs, distribuciones, tendencias, temas y ocupación de un restaurante."""
    name = restaurant["name"]
    meta = restaurant["meta"]
    df = reviews_to_frame(meta)

    # ---------- distribución histórica (perfil de Google) ----------
    distribution = meta.get("reviewsDistribution") or {}
    historical = {
        1: distribution.get("oneStar", 0) or 0,
        2: distribution.get("twoStar", 0) or 0,
        3: distribution.get("threeStar", 0) or 0,
        4: distribution.get("fourStar", 0) or 0,
        5: distribution.get("fiveStar", 0) or 0,
    }
    historical_total = sum(historical.values()) or 1
    historical_positive = historical[4] + historical[5]
    historical_negative = historical[1] + historical[2]

    # ---------- métricas de la muestra reciente ----------
    n = len(df)
    avg_rating = safe_mean(df["rating"])
    recent_counts = {stars: int((df["rating"] == stars).sum()) for stars in range(1, 6)}
    recent_positive = recent_counts[4] + recent_counts[5]
    recent_negative = recent_counts[1] + recent_counts[2]

    if df["publish_dt"].notna().any():
        oldest = df["publish_dt"].min()
        newest = df["publish_dt"].max()
        days_span = max((newest - oldest).days + 1, 1)
    else:
        oldest = newest = None
        days_span = 1

    five_star = df[df["rating"] == 5]
    four_five = df[df["rating"] >= 4]
    text_df = df[df["has_text"]]
    replied = df[df["owner_replied"]]
    negative_sample = df[df["rating"] <= 2]
    negative_three = df[df["rating"] <= 3]
    replied_negative = negative_sample[negative_sample["owner_replied"]]
    replied_negative_three = negative_three[negative_three["owner_replied"]]

    generic_mask = generic_reply_mask(df["reply_norm"]) & df["owner_replied"]
    repeated_mask = repeated_reply_mask(df["owner_reply_text"]) & df["owner_replied"]
    named_mask = df.apply(mentions_name, axis=1)

    language_counts = df["language"].replace("", "desconocido").value_counts()
    total_lang = len(df) or 1

    profile = profile_info(meta)

    overview = {
        "restaurant_name": name,
        "place_id": meta.get("placeId"),
        "category": meta.get("categoryName"),
        "address": meta.get("address"),
        "city": meta.get("city"),
        "state": meta.get("state"),
        "price_range": meta.get("price"),
        "website": meta.get("website"),
        "phone": meta.get("phone"),
        "raw_file": restaurant["raw_file"],
        "total_score_historical": meta.get("totalScore"),
        "reviews_count_historical": meta.get("reviewsCount"),
        "historical_5star_pct": pct(historical[5], historical_total),
        "historical_4star_pct": pct(historical[4], historical_total),
        "historical_3star_pct": pct(historical[3], historical_total),
        "historical_1_2star_pct": pct(historical[1] + historical[2], historical_total),
        "nps_proxy_historical": round(
            (historical_positive - historical_negative) / historical_total * 100, 2
        ),
        "reviews_sample": n,
        "sample_oldest_date": oldest.strftime("%Y-%m-%d") if oldest is not None else None,
        "sample_newest_date": newest.strftime("%Y-%m-%d") if newest is not None else None,
        "days_span": days_span,
        "reviews_per_day": round(n / days_span, 2),
        "reviews_per_month": round(n / days_span * 30, 1),
        "recent_avg_rating": avg_rating,
        "recent_5star_pct": pct(recent_counts[5], n),
        "recent_4star_pct": pct(recent_counts[4], n),
        "recent_3star_pct": pct(recent_counts[3], n),
        "recent_1_2star_pct": pct(recent_negative, n),
        "nps_proxy_recent": round((recent_positive - recent_negative) / n * 100, 2) if n else None,
        "rating_delta_recent_vs_historical": (
            round(avg_rating - float(meta.get("totalScore")), 2)
            if avg_rating is not None and meta.get("totalScore") is not None
            else None
        ),
        "pct_with_text": pct(len(text_df), n),
        "pct_5star_without_text": pct(int((~five_star["has_text"]).sum()), len(five_star)),
        "pct_4_5star_without_text": pct(int((~four_five["has_text"]).sum()), len(four_five)),
        "pct_with_photo": pct(int((df["photos_count"] > 0).sum()), n),
        "avg_photos_per_review": round(df["photos_count"].mean(), 2) if n else None,
        "pct_local_guide": pct(int(df["is_local_guide"].sum()), n),
        "median_reviewer_reviews": df["reviewer_reviews"].median() if n else None,
        "pct_with_detailed_rating": pct(
            int(df[["food_rating", "service_rating", "ambience_rating"]].notna().any(axis=1).sum()), n
        ),
        "avg_food_rating": safe_mean(df["food_rating"]),
        "avg_service_rating": safe_mean(df["service_rating"]),
        "avg_ambience_rating": safe_mean(df["ambience_rating"]),
        "owner_response_rate": pct(len(replied), n),
        "owner_response_rate_1_2star": pct(len(replied_negative), len(negative_sample)),
        "owner_response_rate_1_3star": pct(len(replied_negative_three), len(negative_three)),
        "generic_reply_pct": pct(int(generic_mask.sum()), len(replied)),
        "repeated_reply_pct": pct(int(repeated_mask.sum()), len(replied)),
        "named_reply_pct": pct(int(named_mask.sum()), len(replied)),
        "avg_reply_length": round(replied["owner_reply_text"].str.len().mean(), 1) if len(replied) else None,
        "pct_spanish": pct(int(language_counts.get("es", 0)), total_lang),
        "pct_english": pct(int(language_counts.get("en", 0)), total_lang),
        "pct_other_language": pct(
            int(total_lang - language_counts.get("es", 0) - language_counts.get("en", 0)), total_lang
        ),
        **profile,
    }

    # ---------- tendencia mensual ----------
    current_month = datetime.now().strftime("%Y-%m")
    monthly_rows = []
    if df["year_month"].notna().any():
        for month, group in df.dropna(subset=["year_month"]).groupby("year_month"):
            monthly_rows.append({
                "restaurant_name": name,
                "year_month": month,
                "is_partial_month": month == current_month,
                "reviews": len(group),
                "avg_rating": safe_mean(group["rating"]),
                "pct_1_3star": pct(int((group["rating"] <= 3).sum()), len(group)),
                "pct_4_5star": pct(int((group["rating"] >= 4).sum()), len(group)),
                "pct_with_text": pct(int(group["has_text"].sum()), len(group)),
                "pct_with_reply": pct(int(group["owner_replied"].sum()), len(group)),
                "avg_text_length": round(group["text_length"].mean(), 1) if len(group) else None,
                "pct_with_photo": pct(int((group["photos_count"] > 0).sum()), len(group)),
            })

    # ---------- temas ----------
    topic_rows = build_label_rows(name, text_df, df, TOPICS, "topic")
    product_rows = build_label_rows(name, text_df, df, PRODUCTS, "product")

    # ---------- calidad de respuestas ----------
    response_rows = [{
        "restaurant_name": name,
        "reviews": n,
        "replied": len(replied),
        "response_rate": pct(len(replied), n),
        "reviews_1_2star": len(negative_sample),
        "replied_1_2star": len(replied_negative),
        "response_rate_1_2star": pct(len(replied_negative), len(negative_sample)),
        "reviews_1_3star": len(negative_three),
        "replied_1_3star": len(replied_negative_three),
        "response_rate_1_3star": pct(len(replied_negative_three), len(negative_three)),
        "generic_replies": int(generic_mask.sum()),
        "generic_reply_pct": pct(int(generic_mask.sum()), len(replied)),
        "repeated_replies": int(repeated_mask.sum()),
        "repeated_reply_pct": pct(int(repeated_mask.sum()), len(replied)),
        "named_replies": int(named_mask.sum()),
        "named_reply_pct": pct(int(named_mask.sum()), len(replied)),
        "avg_reply_length": round(replied["owner_reply_text"].str.len().mean(), 1) if len(replied) else None,
    }]

    # ---------- ocupación (popular times) ----------
    occupancy_rows = []
    for day_code, hours in (meta.get("popularTimesHistogram") or {}).items():
        day = DAY_MAP.get(day_code, day_code)
        for entry in hours or []:
            occupancy_rows.append({
                "restaurant_name": name,
                "day": day,
                "hour": entry.get("hour"),
                "occupancy_pct": entry.get("occupancyPercent"),
            })

    # ---------- tags de Google ----------
    tag_rows = []
    for rank, tag in enumerate(meta.get("reviewsTags") or [], start=1):
        tag_rows.append({
            "restaurant_name": name,
            "tag": tag.get("title"),
            "count": tag.get("count"),
            "rank": rank,
        })

    # ---------- competidores ----------
    competitor_rows = []
    for competitor in meta.get("peopleAlsoSearch") or []:
        competitor_rows.append({
            "restaurant_name": name,
            "competitor_name": competitor.get("title"),
            "competitor_reviews": competitor.get("reviewsCount"),
            "competitor_rating": competitor.get("totalScore"),
        })

    # ---------- calidad de datos ----------
    quality_rows = [{
        "restaurant_name": name,
        "raw_file": restaurant["raw_file"],
        "reviews_sample": n,
        "reviews_historical": meta.get("reviewsCount"),
        "oldest_review": oldest.strftime("%Y-%m-%d") if oldest is not None else None,
        "newest_review": newest.strftime("%Y-%m-%d") if newest is not None else None,
        "days_span": days_span,
        "pct_with_text": pct(len(text_df), n),
        "pct_with_review_id": pct(int(df["review_id"].notna().sum()), n),
        "pct_with_detailed_rating": pct(
            int(df[["food_rating", "service_rating", "ambience_rating"]].notna().any(axis=1).sum()), n
        ),
        "pct_with_owner_reply": pct(int(df["owner_replied"].sum()), n),
        "pct_with_language": pct(int((df["language"] != "").sum()), n),
        "pct_with_photos": pct(int((df["photos_count"] > 0).sum()), n),
        "missing_profile_fields": profile["missing_profile_fields"],
    }]

    # ---------- base de reseñas ----------
    reviews = df.copy()
    reviews.insert(0, "restaurant_name", name)
    reviews["topics"] = reviews["text_norm"].apply(lambda x: match_topics(x, TOPICS))
    reviews["products"] = reviews["text_norm"].apply(lambda x: match_topics(x, PRODUCTS))

    return {
        "overview": overview,
        "monthly": monthly_rows,
        "topics": topic_rows,
        "products": product_rows,
        "response": response_rows,
        "occupancy": occupancy_rows,
        "tags": tag_rows,
        "competitors": competitor_rows,
        "quality": quality_rows,
        "reviews": reviews,
    }


def build_label_rows(restaurant_name, text_df, all_df, dictionary, label_column):
    """Filas de análisis para temas o productos (menciones, rating, ejemplos)."""
    rows = []
    total_text = len(text_df)
    restaurant_avg = safe_mean(all_df["rating"])

    for label, pattern in dictionary.items():
        matches = text_df[text_df["text_norm"].apply(lambda text: bool(text and re.search(pattern, text)))]
        mentions = len(matches)
        avg_rating = safe_mean(matches["rating"])
        sample = matches.sort_values("publish_dt", ascending=False).head(1)

        rows.append({
            "restaurant_name": restaurant_name,
            label_column: label,
            "mentions": mentions,
            "pct_of_text_reviews": pct(mentions, total_text),
            "avg_rating": avg_rating,
            "rating_gap_vs_restaurant": (
                round(avg_rating - restaurant_avg, 2)
                if avg_rating is not None and restaurant_avg is not None
                else None
            ),
            "pct_positive": pct(int((matches["rating"] >= 4).sum()), mentions),
            "pct_negative": pct(int((matches["rating"] <= 2).sum()), mentions),
            "sample_rating": int(sample["rating"].iloc[0]) if not sample.empty and pd.notna(sample["rating"].iloc[0]) else None,
            "sample_date": sample["publish_date"].iloc[0] if not sample.empty else None,
            "sample_verbatim": sample["review_text"].iloc[0][:300] if not sample.empty else None,
        })

    return rows


def occupancy_tables(rows):
    """Devuelve la ocupación en formato largo y el resumen por restaurante."""
    empty_long = pd.DataFrame(columns=OCCUPANCY_COLUMNS)
    empty_summary = pd.DataFrame(columns=OCCUPANCY_SUMMARY_COLUMNS)

    df = pd.DataFrame(rows)
    if df.empty:
        return empty_long, empty_summary

    df = df.dropna(subset=["hour", "occupancy_pct"]).copy()
    if df.empty:
        return empty_long, empty_summary

    # Google rellena con 0 las horas en que el local está cerrado. Si se
    # incluyen, la ocupación media y las "horas valle" quedan distorsionadas
    # (p. ej. un local que abre solo a la noche parecería vacío todo el día).
    df = df[df["occupancy_pct"] > 0].copy()
    if df.empty:
        return empty_long, empty_summary

    df["hour"] = df["hour"].astype(int)

    by_hour = (
        df.groupby(["restaurant_name", "hour"])["occupancy_pct"]
        .agg(avg="mean", max="max", min="min")
        .reset_index()
    )
    by_day = (
        df.groupby(["restaurant_name", "day"])["occupancy_pct"]
        .agg(avg="mean")
        .reset_index()
    )

    summaries = []
    for name, group in by_hour.groupby("restaurant_name"):
        peak = group.loc[group["avg"].idxmax()]
        dead_hours = group.loc[group["avg"] < 25, "hour"].tolist()
        day_group = by_day[by_day["restaurant_name"] == name]
        busiest_day = day_group.loc[day_group["avg"].idxmax()]
        summaries.append({
            "restaurant_name": name,
            "peak_hour": int(peak["hour"]),
            "peak_hour_avg_occupancy_pct": round(float(peak["avg"]), 1),
            "busiest_day": busiest_day["day"],
            "busiest_day_avg_occupancy_pct": round(float(busiest_day["avg"]), 1),
            "dead_hours_lt25": ", ".join(str(int(hour)) for hour in dead_hours),
            "avg_occupancy_pct": round(float(group["avg"].mean()), 1),
        })

    return df[OCCUPANCY_COLUMNS], pd.DataFrame(summaries, columns=OCCUPANCY_SUMMARY_COLUMNS)


def write_table(file_name, data, columns):
    """Escribe un CSV con columnas estables y reporta su tamaño."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        df = pd.DataFrame(data)

    df = df.reindex(columns=columns)
    path = PROCESSED_DIR / file_name
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"✅ {file_name}: {len(df)} filas")
    return {"table": file_name, "rows": len(df), "columns": len(columns)}


OUTPUT_TABLES = [
    "restaurants.csv",
    "reviews.csv",
    "monthly_trend.csv",
    "themes.csv",
    "occupancy.csv",
    "competitors.csv",
]


def merge_restaurant_rows(overview_rows, response_rows, profile_rows, quality_rows,
                          occ_summary_rows, generated_at):
    """Fusiona todos los KPIs a nivel restaurante en una sola fila por restaurante."""
    merged = {row["restaurant_name"]: dict(row) for row in overview_rows}

    extra_fields = [
        (
            response_rows,
            [
                "replied", "reviews_1_2star", "replied_1_2star",
                "reviews_1_3star", "replied_1_3star",
                "generic_replies", "repeated_replies", "named_replies",
            ],
        ),
        (
            profile_rows,
            [
                key for key in PROFILE_COLUMNS
                if key not in ("restaurant_name", "profile_score", "missing_profile_fields")
            ],
        ),
        (quality_rows, ["pct_with_review_id", "pct_with_language"]),
        (
            occ_summary_rows,
            [key for key in OCCUPANCY_SUMMARY_COLUMNS if key != "restaurant_name"],
        ),
    ]

    for rows, fields in extra_fields:
        for row in rows:
            target = merged.get(row.get("restaurant_name"))
            if target is None:
                continue
            for field in fields:
                target[field] = row.get(field)

    for row in merged.values():
        row["generated_at"] = generated_at

    return list(merged.values())


def build_theme_rows(topic_rows, product_rows, tag_rows):
    """Une temas, productos y etiquetas de Google en una sola tabla larga."""
    rows = []

    for row in topic_rows:
        rows.append({
            "restaurant_name": row["restaurant_name"],
            "dimension": "Tema",
            "label": row["topic"],
            "mentions": row["mentions"],
            "pct_of_text_reviews": row["pct_of_text_reviews"],
            "avg_rating": row["avg_rating"],
            "rating_gap_vs_restaurant": row["rating_gap_vs_restaurant"],
            "pct_positive": row["pct_positive"],
            "pct_negative": row["pct_negative"],
            "rank": None,
            "sample_rating": row["sample_rating"],
            "sample_date": row["sample_date"],
            "sample_verbatim": row["sample_verbatim"],
        })

    for row in product_rows:
        rows.append({
            "restaurant_name": row["restaurant_name"],
            "dimension": "Producto",
            "label": row["product"],
            "mentions": row["mentions"],
            "pct_of_text_reviews": row["pct_of_text_reviews"],
            "avg_rating": row["avg_rating"],
            "rating_gap_vs_restaurant": row["rating_gap_vs_restaurant"],
            "pct_positive": row["pct_positive"],
            "pct_negative": row["pct_negative"],
            "rank": None,
            "sample_rating": row["sample_rating"],
            "sample_date": row["sample_date"],
            "sample_verbatim": row["sample_verbatim"],
        })

    for row in tag_rows:
        rows.append({
            "restaurant_name": row["restaurant_name"],
            "dimension": "Etiqueta Google",
            "label": row["tag"],
            "mentions": row["count"],
            "pct_of_text_reviews": None,
            "avg_rating": None,
            "rating_gap_vs_restaurant": None,
            "pct_positive": None,
            "pct_negative": None,
            "rank": row["rank"],
            "sample_rating": None,
            "sample_date": None,
            "sample_verbatim": None,
        })

    return rows


def cleanup_obsolete_tables(keep):
    """Elimina CSV antiguos para que processed contenga solo las 6 tablas nuevas."""
    removed = []
    for path in sorted(PROCESSED_DIR.glob("*.csv")):
        if path.name not in keep:
            path.unlink()
            removed.append(path.name)

    if removed:
        print(f"🧹 Tablas obsoletas eliminadas: {len(removed)}")
        for name in removed:
            print(f"   • {name}")


def main():
    print("🚀 Generando tablas de análisis (sin IA, 100% determinista)...")

    restaurants = load_restaurants()
    print(f"📂 Restaurantes encontrados: {len(restaurants)}")

    overview_rows = []
    monthly_rows = []
    topic_rows = []
    product_rows = []
    response_rows = []
    occupancy_rows = []
    tag_rows = []
    competitor_rows = []
    quality_rows = []
    review_frames = []
    profile_rows = []

    for restaurant in restaurants:
        print(f"   • {restaurant['name']}")
        result = build_restaurant_metrics(restaurant)

        overview_rows.append(result["overview"])
        monthly_rows.extend(result["monthly"])
        topic_rows.extend(result["topics"])
        product_rows.extend(result["products"])
        response_rows.extend(result["response"])
        occupancy_rows.extend(result["occupancy"])
        tag_rows.extend(result["tags"])
        competitor_rows.extend(result["competitors"])
        quality_rows.extend(result["quality"])
        review_frames.append(result["reviews"])

        profile_rows.append({
            "restaurant_name": result["overview"]["restaurant_name"],
            **{key: result["overview"][key] for key in PROFILE_COLUMNS if key in result["overview"]},
        })

    # Base de reseñas para filtros y métricas derivadas del dashboard
    reviews_df = pd.concat(review_frames, ignore_index=True) if review_frames else pd.DataFrame()
    if not reviews_df.empty:
        reviews_df = reviews_df.sort_values(
            by=["restaurant_name", "publish_dt"], ascending=[True, False], na_position="last"
        ).reset_index(drop=True)

    occ_long, occ_summary = occupancy_tables(occupancy_rows)
    theme_rows = build_theme_rows(topic_rows, product_rows, tag_rows)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    restaurant_rows = merge_restaurant_rows(
        overview_rows,
        response_rows,
        profile_rows,
        quality_rows,
        occ_summary.to_dict("records"),
        generated_at,
    )

    write_table("restaurants.csv", restaurant_rows, RESTAURANTS_COLUMNS)
    write_table("reviews.csv", reviews_df, REVIEWS_COLUMNS)
    write_table("monthly_trend.csv", monthly_rows, MONTHLY_COLUMNS)
    write_table("themes.csv", theme_rows, THEMES_COLUMNS)
    write_table("occupancy.csv", occ_long, OCCUPANCY_COLUMNS)
    write_table("competitors.csv", competitor_rows, COMPETITOR_COLUMNS)

    cleanup_obsolete_tables(set(OUTPUT_TABLES))

    print(f"\n✨ Listo. Tablas guardadas en: {PROCESSED_DIR}")
    print(f"📊 {len(OUTPUT_TABLES)} tablas generadas para Streamlit.")


if __name__ == "__main__":
    main()
