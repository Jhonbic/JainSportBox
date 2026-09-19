"""Tipos de medición de las marcas (récords personales).

Vive fuera de los routers porque lo comparten tres lugares: el catálogo de
ejercicios (que es donde el admin elige el tipo), el router de marcas (que
valida los campos según el tipo) y el seed. Con la regla escrita en cada uno,
agregar un tipo nuevo obliga a acordarse de los tres.

Espeja a `frontend/src/data/ejerciciosMarcas.js` — mantener en sincronía.
"""

# barra            → peso EXTERNO + reps → 1RM (promedio de 7 fórmulas).
#                    Ojo con el nombre: no es solo barra. Sirve para cualquier peso
#                    (mancuerna, kettlebell, máquina); quedó así de cuando la lista
#                    eran 7 levantamientos fijos y todos eran con barra. En pantalla
#                    se rotula "Peso levantado" — el valor guardado no se renombró
#                    porque ya está en la base y en las marcas cargadas.
# corporal_lastre  → peso corporal (de Mi Salud) + lastre opcional + reps → 1RM
# reps             → solo repeticiones máximas (sin 1RM)
# leger            → nivel + palier (sin peso ni reps)
TIPOS_MARCA = ("barra", "corporal_lastre", "reps", "leger")

# Los tipos con los que arrancó el módulo, cuando la lista era fija en el
# frontend. `seed_tipos_marca()` los aplica UNA sola vez sobre el catálogo ya
# sembrado; después manda lo que configure el staff. Los nombres coinciden con
# los de `EJERCICIOS_DEFAULT` en seed.py, que es lo que hizo posible unificar
# los dos catálogos sin migrar una sola fila de `marcas_rm`.
TIPOS_MARCA_DEFAULT = {
    "Back Squat": "barra",
    "Deadlift": "barra",
    "Clean": "barra",
    "Clean and Jerk": "barra",
    "Snatch": "barra",
    "Bench Press": "barra",
    "Press Militar": "barra",
    "Dominadas": "corporal_lastre",
    "Push Up": "reps",
    "Air Squat": "reps",
    "Sit Up": "reps",
    "Test de Léger": "leger",
}
