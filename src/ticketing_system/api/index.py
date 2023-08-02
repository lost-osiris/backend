from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from dotenv import load_dotenv
import os

ENV = f".{os.getenv('ENV')}" or ""
load_dotenv(f".env{ENV}")

from .routes import issue, project, user, db_updates, issue_comments, cron_jobs, blogs
from . import auth

app = FastAPI()

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(auth.router)
app.include_router(issue.router)
app.include_router(issue_comments.router)
app.include_router(project.router)
app.include_router(user.router)
app.include_router(db_updates.router)
app.include_router(cron_jobs.router)
app.include_router(blogs.router)
