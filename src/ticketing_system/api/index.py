from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os

ENV = f".{os.getenv('ENV')}" or ""
load_dotenv(f".env{ENV}")

from . import auth
from .routes import issue, project, user, db_updates, issue_comments
from .routes import cron_jobs, blogs

app = FastAPI()
origins = [
    "https://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(auth.router)
app.include_router(issue.router)
app.include_router(issue_comments.router)
app.include_router(project.router)
app.include_router(user.router)
app.include_router(db_updates.router)
app.include_router(cron_jobs.router)
app.include_router(blogs.router)
