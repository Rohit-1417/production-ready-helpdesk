from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "Welcome to the Helpdesk Management System!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }





app.include_router(auth_router)
app.include_router(admin_router)