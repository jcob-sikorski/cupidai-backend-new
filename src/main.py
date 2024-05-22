from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os

import uvicorn

from web import (
    account, ai_verification, billing, bug, deepfake,
    image_generation, midjourney, referral, usage_history
    # team
)

app = FastAPI()

origins = [
    os.getenv("WEBAPP_DOMAIN"),
    os.getenv("LANDING_DOMAIN"),
    os.getenv("RUNPOD_DOMAIN")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(account.router)
app.include_router(ai_verification.router)
app.include_router(billing.router)
app.include_router(bug.router)
app.include_router(deepfake.router)
app.include_router(usage_history.router)
app.include_router(image_generation.router)
app.include_router(midjourney.router)
app.include_router(referral.router)
# app.include_router(team.router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)