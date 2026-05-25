from contextlib import asynccontextmanager
from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from app.routers import webhook
from app.services.jobs import job_resumo_bidiario, job_resumo_diario

BRT = pytz.timezone("America/Sao_Paulo")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler(timezone=BRT)

    scheduler.add_job(
        job_resumo_diario,
        CronTrigger(hour=6, minute=0, timezone=BRT),
        id="resumo_diario",
        name="Resumo diário de gastos",
    )

    scheduler.add_job(
        job_resumo_bidiario,
        IntervalTrigger(
            days=2,
            start_date=datetime(2026, 5, 26, 8, 0, 0, tzinfo=BRT),
            timezone=BRT,
        ),
        id="resumo_bidiario",
        name="Resumo bidiário do mês",
    )

    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="bot-finanpessoal", version="0.1.0", lifespan=lifespan)

app.include_router(webhook.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
