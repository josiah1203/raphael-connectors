"""Raphael connectors service."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from raphael_contracts.errors import ErrorResponse
from raphael_connectors.routes import router

app = FastAPI(title="raphael-connectors", version="0.1.0")
app.include_router(router, prefix="/v1/connectors")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "raphael-connectors"}


@app.exception_handler(Exception)
async def unhandled(_request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=ErrorResponse(code="internal_error", message=str(exc)).model_dump())
