"""
Rate limiting ligero en memoria (ventana deslizante) para mitigar fuerza bruta y
abuso en endpoints públicos (login, registro).

Sin dependencias externas ni Redis: el estado vive en el proceso. Con varios
workers de uvicorn el límite es por-worker (el efectivo es N×límite), suficiente
como mitigación básica. Para un límite global estricto se necesitaría un store
compartido (Redis) — documentado como mejora futura.
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

_lock = threading.Lock()
_hits: dict = defaultdict(deque)  # (bucket, ip) -> deque[timestamps]


def _client_ip(request: Request) -> str:
    # Detrás del proxy de Railway la IP real viene en X-Forwarded-For.
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "desconocido"


def limitar(bucket: str, max_requests: int, window_seconds: int):
    """Devuelve una dependencia de FastAPI que aplica el límite indicado por IP."""

    def _dep(request: Request) -> None:
        ahora = time.monotonic()
        corte = ahora - window_seconds
        clave = (bucket, _client_ip(request))
        with _lock:
            cola = _hits[clave]
            while cola and cola[0] < corte:
                cola.popleft()
            if len(cola) >= max_requests:
                reintento = int(cola[0] + window_seconds - ahora) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Demasiados intentos. Espera un momento e inténtalo de nuevo.",
                    headers={"Retry-After": str(max(1, reintento))},
                )
            cola.append(ahora)

    return _dep
