from app.core.config import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.core.config:app", host="0.0.0.0", port=8000, reload=True)