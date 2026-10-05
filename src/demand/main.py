from demand.ops import router as ops_router
from fastapi import FastAPI, HTTPException
from demand.forecast import InputError, forecast

app = FastAPI()
app.include_router(ops_router, prefix="/v1")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/forecast")
def post_forecast(body: dict):
    try:
        return forecast(body.get("series"))
    except InputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
