from fastapi import APIRouter

from model.midjourney import Message

from service import midjourney as service

from typing import Any
from fastapi import Body, FastAPI

router = APIRouter(prefix = "/midjourney")


@router.post("/webhook", status_code=201)
async def webhook(message: Message) -> None:
    print("MIDJOURNEY WEBHOOK ACTIVATED")
    print(message)
    return service.webhook(message)