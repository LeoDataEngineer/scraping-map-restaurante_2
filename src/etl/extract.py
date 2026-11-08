import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

from apify_client import ApifyClient

# Evitar errores de codificación con emojis en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Rutas del proyecto (funcionan sin importar desde dónde se ejecute el script)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CREDENTIALS_PATH = PROJECT_ROOT / "credentials" / "apify_token.txt"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# ID del Actor de Google Maps Scraper
ACTOR_ID = "nwua9Gu5YrADL7ZDj"

# ==========================================
# Restaurantes a extraer
# ==========================================
# Agrega tantos restaurantes como quieras. Solo necesitas el ID de Google Maps.
# "name" es opcional: si lo omites, se usará el nombre que devuelve Google Maps.
PLACES = [
    {"place_id": "ChIJhQCBJUq1vJURSM8pEx4htow", "name": "ORNO Guatemala"},
    #{"place_id": "ChIJEwSWuaSP", "name": ""},
    # {"place_id": "ChIJyyyyyyyyyyyyyyyyyyyyyy", "name": "Otro Restaurante"},
]


def load_apify_token():
    """Lee el token de Apify desde la variable de entorno APIFY_TOKEN o desde credentials/apify_token.txt."""
    token = os.getenv("APIFY_TOKEN")
    if token and token.strip():
        return token.strip()

    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"❌ No se encontró el token de Apify. "
            f"Define la variable de entorno APIFY_TOKEN o crea el archivo '{CREDENTIALS_PATH}'."
        )

    token = CREDENTIALS_PATH.read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError(f"❌ El archivo '{CREDENTIALS_PATH}' está vacío.")

    return token


def slugify(text):
    """Convierte un nombre en un identificador seguro para nombres de archivo.

    Ej: "ORNO Guatemala" -> "orno_guatemala"
    """
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text or "restaurante"


def build_run_input(place_ids):
    """Construye la configuración del Actor para todos los restaurantes."""
    return {
        "placeIds": place_ids,
        "maxReviews": 2000,
        "reviewsSort": "newest",
        "language": "es",
        "reviewsLanguage": "es",
        "scrapePlaceDetailPage": True,
        "scrapeReviewsPersonalData": True,
        "searchStringsArray": [],
        "locationQuery": "",
        "countryCode": "ar",
        "city": "Cdad. Autónoma de Buenos Aires",
        "state": "Cdad. Autónoma de Buenos Aires"
    }


def save_raw_by_place(items, places):
    """Agrupa los resultados por restaurant y guarda un JSON por cada uno.

    Nombre generado: <nombre_restaurante>_apify_raw_data_<fecha>.json
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Agrupar los elementos del dataset por placeId
    items_by_place = {}
    for item in items:
        keys = {
            item.get("placeId"),
            item.get("inputPlaceId"),
            item.get("queryPlaceId"),
        }
        for key in keys:
            if key:
                items_by_place.setdefault(key, []).append(item)

    saved_files = []
    used_slugs = set()

    for place in places:
        place_id = place["place_id"]
        place_items = items_by_place.get(place_id, [])

        if not place_items:
            print(f"⚠️ No se obtuvieron datos para el place_id '{place_id}'. Se omite.")
            continue

        # Nombre: el configurado o el que devuelve Google Maps
        restaurant_name = place.get("name") or place_items[0].get("title") or place_id
        slug = slugify(restaurant_name)

        # Evitar colisiones si dos restaurantes generan el mismo slug
        if slug in used_slugs:
            slug = f"{slug}_{slugify(place_id)[-6:]}"
        used_slugs.add(slug)

        file_path = RAW_DIR / f"{slug}_apify_raw_data_{current_date}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(place_items, f, ensure_ascii=False, indent=4)

        saved_files.append(file_path)
        print(f"💾 Datos crudos guardados: '{file_path.name}' ({len(place_items)} elemento(s))")

    return saved_files


def run_extraction(places=None):
    """Extrae los datos de uno o varios restaurantes y guarda un JSON crudo por cada uno."""
    places = places or PLACES
    if not places:
        raise ValueError("❌ Debes indicar al menos un restaurante en la lista PLACES.")

    print(f"🚀 Iniciando la extracción de {len(places)} restaurante(s) desde Apify...")

    # Inicializar el cliente con el token de Apify (nunca escrito en el código)
    client = ApifyClient(load_apify_token())

    place_ids = [place["place_id"] for place in places]

    # Ejecutar el Actor una sola vez con todos los restaurantes
    run = client.actor(ACTOR_ID).call(run_input=build_run_input(place_ids))

    # Obtener el dataset ID de forma segura
    run_dict = run.model_dump() if hasattr(run, 'model_dump') else dict(run)
    dataset_id = run_dict.get("defaultDatasetId") or run_dict.get("default_dataset_id")

    if not dataset_id:
        last_run = client.actor(ACTOR_ID).last_run()
        last_run_dict = last_run.model_dump() if hasattr(last_run, 'model_dump') else dict(last_run)
        dataset_id = last_run_dict.get("defaultDatasetId") or last_run_dict.get("default_dataset_id")

    print(f"📦 Dataset ID obtenido con éxito: {dataset_id}")

    # Recolectar todos los resultados en una lista
    items = list(client.dataset(dataset_id).iterate_items())
    print(f"✅ Descarga finalizada. Total de elementos obtenidos: {len(items)}")

    # Guardar un archivo por restaurante, con su nombre al inicio
    saved_files = save_raw_by_place(items, places)

    if not saved_files:
        print("⚠️ No se guardó ningún archivo. Revisa los place_id configurados.")
    else:
        print(f"✨ Extracción completada. Archivos generados: {len(saved_files)}")

    return saved_files


if __name__ == "__main__":
    run_extraction()
