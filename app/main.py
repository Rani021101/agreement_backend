from .auth import router as auth_router
from .agreements import router as agreement_router, check_agreement_reminders
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

origins = [
    "https://rani021101.github.io",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(agreement_router)


scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(
        check_agreement_reminders,
        "cron",
        hour=1,
        minute=0 # your database connection
    )
    scheduler.start()

@app.on_event("startup")
def startup_event():
    start_scheduler()