# app/core/websocket_manager.py
from fastapi import WebSocket
from typing import List

# connection_manager.py

class ConnectionManager:
    def __init__(self):
        self.active_esps = {}     
        self.active_mobiles = {}   

    async def connect_esp(self, esp_mac_address: str, websocket: WebSocket):
        await websocket.accept()
        self.active_esps[esp_mac_address] = websocket

    async def connect_mobile(self, esp_mac_address: str, websocket: WebSocket):
        await websocket.accept()
        self.active_mobiles[esp_mac_address] = websocket

    async def disconnect_esp(self, esp_mac_address: str):
        self.active_esps.pop(esp_mac_address, None)
        self.active_mobiles.pop(esp_mac_address, None)

    async def disconnect_mobile(self, esp_mac_address: str):
        self.active_mobiles.pop(esp_mac_address, None)

    async def send_to_esp(self, esp_mac_address: str, message: dict):
        ws = self.active_esps.get(esp_mac_address)
        if ws:
            await ws.send_json(message)

    async def send_to_mobile(self, esp_mac_address: str, message: dict):
        ws = self.active_mobiles.get(esp_mac_address)
        if ws:
            await ws.send_json(message)

manager = ConnectionManager()