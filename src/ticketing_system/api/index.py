from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from dotenv import load_dotenv

load_dotenv()

from .routes import issue, project, user, db_updates

app = FastAPI()

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(issue.router)
app.include_router(project.router)
app.include_router(user.router)
app.include_router(db_updates.router)
