from fastapi import FastAPI
from .routes import issue, project, user, db_updates

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.include_router(issue.router)
app.include_router(project.router)
app.include_router(user.router)
app.include_router(db_updates.router)
