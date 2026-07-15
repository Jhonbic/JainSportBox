"""§12 de tests.md (Fase 5) — Coherencia de los bloques de migración de main.py.

Sin un Postgres real disponible, esta verificación es estática pero cubre la
clase de bug que ya ocurrió en Railway ("no deja crear WODs"): una columna
agregada solo al bloque SQLite falta en Postgres porque create_all no agrega
columnas a tablas existentes.

Reglas verificadas:
1. Toda columna del bloque SQLite (_migraciones) está también en el bloque
   Postgres (_cols_pg).
2. Toda columna de ambos bloques existe en los modelos (detecta typos/renames).
3. Todo índice del bloque _indices referencia tabla y columnas reales.

La ejecución real del bloque SQLite ya se cubre en cada corrida de la suite:
el conftest importa main contra una BD temporal limpia.
"""

import re
from pathlib import Path

import models

MAIN_SRC = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")

RE_SQLITE = re.compile(r'"ALTER TABLE (\w+) ADD COLUMN (\w+)')
RE_PG = re.compile(r'"ALTER TABLE (\w+) ADD COLUMN IF NOT EXISTS (\w+)')
RE_INDICE = re.compile(r'"CREATE INDEX IF NOT EXISTS \w+ ON (\w+) \(([^)]+)\)"')


def _columnas_modelo():
    return {
        (tabla.name, col.name)
        for tabla in models.Base.metadata.tables.values()
        for col in tabla.columns
    }


def _bloque_sqlite():
    # el patrón PG también matchea el prefijo "ALTER TABLE x ADD COLUMN" con
    # columna "IF": excluir los del bloque Postgres
    pares = set(RE_SQLITE.findall(MAIN_SRC))
    return {p for p in pares if p[1] != "IF"}


def _bloque_pg():
    return set(RE_PG.findall(MAIN_SRC))


def test_parsers_encuentran_los_bloques():
    assert len(_bloque_sqlite()) >= 25
    assert len(_bloque_pg()) >= 25


def test_toda_columna_sqlite_esta_en_postgres():
    """Regla de CLAUDE.md: agregar una columna exige tocar AMBOS bloques."""
    faltantes = _bloque_sqlite() - _bloque_pg()
    assert not faltantes, (
        f"Columnas migradas solo en SQLite (faltarán en Railway/Postgres): {sorted(faltantes)}"
    )


def test_columnas_migradas_existen_en_los_modelos():
    modelo = _columnas_modelo()
    fantasmas = (_bloque_sqlite() | _bloque_pg()) - modelo
    assert not fantasmas, f"Migraciones a columnas que no existen en models.py: {sorted(fantasmas)}"


def test_indices_referencian_columnas_reales():
    modelo = _columnas_modelo()
    tablas = {t for t, _ in modelo}
    indices = RE_INDICE.findall(MAIN_SRC)
    assert len(indices) >= 15
    for tabla, cols in indices:
        assert tabla in tablas, f"Índice sobre tabla inexistente: {tabla}"
        for col in (c.strip() for c in cols.split(",")):
            assert (tabla, col) in modelo, f"Índice sobre columna inexistente: {tabla}.{col}"
