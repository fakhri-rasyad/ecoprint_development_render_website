import firebase_admin
from firebase_admin import credentials, messaging
from app.core.enum.enum_classes import Status
from dotenv import load_dotenv
from os import getenv
import logging
from sqlmodel import Session as SQLSession, select
from app.database.database_model.esp_database_model import ESP
from app.database.database_model.user_model import User
from app.database.database import engine
import asyncio

logger = logging.getLogger("global")

load_dotenv()


class FirebaseSDK:
    def __init__(self):
        try:
            file_path = getenv("GOOGLE_APPLICATION_CREDENTIALS")

            if not firebase_admin._apps:
                cred = credentials.Certificate(file_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized")
            else:
                logger.info("Firebase already initialized, skipping")

        except Exception:
            logger.exception("Failure on starting Firebase")

    def send_message(self, esp_mac: str, event: Status):
        with SQLSession(engine) as session:
            stmt = select(ESP.user_id).where(ESP.esp_mac_address == esp_mac)
            user_id = session.exec(stmt).first()

            if not user_id:
                logger.error("No active user for ESP %s", esp_mac)
                return
            
            user_id = user_id 

            stmt = select(User.fcm_token).where(User.id == user_id)
            token = session.exec(stmt).first()

        if not token:
            logger.error("User %s has no FCM token", user_id)
            return

        status_text = (
            "Pengukusan Dibatalkan" if event == Status.CANCELED 
            else "Pengukusan Selesai!"
        )

        message = messaging.Message(
            notification=messaging.Notification(
                title=str(event.value),
                body=status_text,
            ),
            token=token,
        )

        try:
            response = messaging.send(message)
            logger.info("Successfully sent message: %s", response)
        except Exception:
            logger.exception("Failed sending message")

    async def send_message_async(self, esp_mac: str, event: Status):
        await asyncio.to_thread(self.send_message, esp_mac, event)

firebase = FirebaseSDK()
