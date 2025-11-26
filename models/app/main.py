from fastapi import FastAPI
from theia.config import settings
from theia.logging import setup_logging
from theia.middleware.correlation import CorrelationMiddleware
from theia.middleware.persona import PersonaMiddleware

from theia_api.app.routes import mirror as mirror_routes  # <— add this

app = FastAPI(title="THEIA API", version="v1")


@app.on_event("startup")
def _startup():
    setup_logging(settings.log_level, static_fields={"service": "theia-api", "env": settings.env})
    import logging
    logging.getLogger("startup").info("settings=%s", settings.safe_dump())


app.add_middleware(CorrelationMiddleware)
app.add_middleware(PersonaMiddleware)

app.include_router(mirror_routes.router)  # <— mount /api/mirror
