from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import repositories, questions, audio

app = FastAPI(
    title="AI Code Explainer API",
    description="API for the AI Code Explainer service using Google Gemini",
    version="0.1.0"
)

# Configure CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with your Next.js frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from endpoints
app.include_router(repositories.router, prefix="/api/repositories", tags=["repositories"])
app.include_router(questions.router, prefix="/api/questions", tags=["questions"])
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Code Explainer API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)