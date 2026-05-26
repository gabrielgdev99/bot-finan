from contextlib import asynccontextmanager
from datetime import datetime

import subprocess

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from app.routers import webhook
from app.services.jobs import job_resumo_bidiario, job_resumo_diario, job_comparativo_mensal, job_processar_lembretes

BRT = pytz.timezone("America/Sao_Paulo")


@asynccontextmanager
async def lifespan(app: FastAPI):
    subprocess.run(["alembic", "upgrade", "head"], check=True)

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

    scheduler.add_job(
        job_comparativo_mensal,
        CronTrigger(day=1, hour=8, minute=0, timezone=BRT),
        id="comparativo_mensal",
        name="Comparativo mensal do dia 1",
    )

    scheduler.add_job(
        job_processar_lembretes,
        CronTrigger(hour=8, minute=0, timezone=BRT),
        id="processar_lembretes",
        name="Processar lembretes (avisos e lançamentos automáticos)",
    )

    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="bot-finanpessoal", version="0.1.0", lifespan=lifespan)

app.include_router(webhook.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
