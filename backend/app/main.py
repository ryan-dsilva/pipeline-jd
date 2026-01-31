from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, jobs, pipeline, sections

app = FastAPI(title="AppV2 Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(pipeline.router)
app.include_router(sections.router)
app.include_router(sections.section_definitions_router)
app.include_router(chat.router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "AppV2 Pipeline API"}
