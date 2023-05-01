from fastapi import FastAPI
from .routes import issue, project, user

app = FastAPI()
app.include_router(issue.router)
app.include_router(project.router)
app.include_router(user.router)
