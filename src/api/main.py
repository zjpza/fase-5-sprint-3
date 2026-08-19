from __future__ import annotations

import sys
from pathlib import Path

# Adiciona a raiz do projeto ao PYTHONPATH para importar src.*
FILE_ROOT = Path(__file__).resolve().parent
ROOT = FILE_ROOT.parents[1]  # src/api/main.py -> src/api -> src -> raiz
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# Também adiciona src para compatibilidade com execução via `python src/api/main.py`
SRC_ROOT = FILE_ROOT.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fastapi import FastAPI

from api.routes import router

app = FastAPI(
    title="AgroRisk AI API",
    description="Backend integrador da Sprint 3 — predição de risco operacional em frotas agrícolas.",
    version="3.0.0",
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "agrorisk-api", "version": "3.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
