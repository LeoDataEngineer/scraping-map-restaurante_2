"""Orquestador del pipeline ETL.

Ejecuta en orden los dos scripts de src/etl/:
    1. extract.py     -> datos raw de Apify en data/raw/
    2. transform.py   -> 6 tablas de negocio en data/processed/

Uso:
    python src/run_etl.py
    python src/run_etl.py --skip-extract
    python src/run_etl.py --skip-transform
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Evitar errores de codificación con emojis en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ETL_DIR = PROJECT_ROOT / "src" / "etl"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Ejecuta el pipeline ETL completo (extract -> transform)."
    )
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="Omite la extracción desde Apify.",
    )
    parser.add_argument(
        "--skip-transform",
        action="store_true",
        help="Omite la transformación y usa las tablas existentes en data/processed/.",
    )
    return parser.parse_args(argv)


def build_steps(args):
    """Devuelve la lista de pasos a ejecutar según los flags recibidos."""
    steps = []

    if not args.skip_extract:
        steps.append(("Extract", ETL_DIR / "extract.py", []))

    if not args.skip_transform:
        steps.append(("Transform", ETL_DIR / "transform.py", []))

    return steps


def run_step(name, script, extra_args):
    """Ejecuta un script ETL y devuelve su código de salida."""
    print(f"\n{'=' * 60}")
    print(f"▶️  {name}: {script.relative_to(PROJECT_ROOT)}")
    print(f"{'=' * 60}")

    if not script.exists():
        print(f"❌ No se encontró el script: {script}")
        return 1

    command = [sys.executable, str(script), *extra_args]
    print(f"$ {' '.join(command)}\n")

    started = time.perf_counter()
    try:
        completed = subprocess.run(command, cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print(f"\n⚠️  {name} interrumpido por el usuario.")
        return 130

    elapsed = time.perf_counter() - started
    if completed.returncode != 0:
        print(f"\n❌ {name} falló con código {completed.returncode} ({elapsed:.1f}s).")
        return completed.returncode

    print(f"\n✅ {name} completado en {elapsed:.1f}s.")
    return 0


def main(argv=None):
    args = parse_args(argv)
    steps = build_steps(args)

    if not steps:
        print("⚠️  No hay pasos para ejecutar: todos fueron omitidos.")
        return 0

    print("🚀 Orquestador ETL")
    print(f"📂 Proyecto: {PROJECT_ROOT}")
    print(f"🧩 Pasos: {' -> '.join(name for name, _, _ in steps)}")

    started = time.perf_counter()
    for name, script, extra_args in steps:
        code = run_step(name, script, extra_args)
        if code != 0:
            print("\n⛔ Pipeline detenido.")
            return code

    elapsed = time.perf_counter() - started
    print(f"\n{'=' * 60}")
    print(f"✨ Pipeline completado en {elapsed:.1f}s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
