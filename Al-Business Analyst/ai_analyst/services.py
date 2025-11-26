import google.generativeai as genai
import json
import base64
import asyncio
import time
import os
from datetime import datetime
from typing import Dict, Optional
from PIL import Image
from config import GOOGLE_API_KEY
from prompts import SYSTEM_PROMPT

# Настройка Google API
genai.configure(api_key=GOOGLE_API_KEY)

# Хранилище чатов {user_id: chat_session}
# В Google API есть удобный объект ChatSession, который сам помнит историю
chats = {}

# Хранилище метрик времени {user_id: {"start_time": ..., "messages_count": ...}}
metrics = {}

async def get_ai_response(user_id: int, user_text: str):
    try:
        # Инициализация метрик для нового диалога
        if user_id not in metrics:
            metrics[user_id] = {
                "start_time": time.time(),
                "messages_count": 0,
                "first_message_time": None
            }
        
        metrics[user_id]["messages_count"] += 1
        if metrics[user_id]["first_message_time"] is None:
            metrics[user_id]["first_message_time"] = time.time()
        
        # 1. Создаем или достаем сессию чата
        if user_id not in chats:
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=SYSTEM_PROMPT
            )
            chats[user_id] = model.start_chat(history=[])
        
        chat = chats[user_id]
        
        # 2. Отправляем сообщение (синхронный вызов в executor для асинхронности)
        start_request = time.time()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, chat.send_message, user_text)
        request_time = time.time() - start_request
        
        ai_text = response.text
        
        # 3. Проверяем, не вернул ли он JSON (финал)
        clean_text = ai_text.replace("```json", "").replace("```", "").strip()
        
        try:
            if "{" in clean_text and "}" in clean_text:
                data = json.loads(clean_text)
                if data.get("status") == "completed":
                    # Вычисляем общее время формирования требований
                    total_time = time.time() - metrics[user_id]["first_message_time"]
                    data["metrics"] = {
                        "total_time_seconds": round(total_time, 2),
                        "total_time_minutes": round(total_time / 60, 2),
                        "messages_count": metrics[user_id]["messages_count"],
                        "last_request_time": round(request_time, 2)
                    }
                    # Очищаем метрики после завершения
                    if user_id in metrics:
                        del metrics[user_id]
                    return {"type": "final", "data": data}
        except json.JSONDecodeError:
            pass # Значит это просто текст вопроса
            
        return {"type": "text", "text": ai_text}
    except Exception as e:
        return {"type": "error", "text": str(e)}

async def get_ai_response_with_image(user_id: int, user_text: str, image_path: str):
    """Обрабатывает сообщение с изображением через Gemini Vision"""
    try:
        # Инициализация метрик
        if user_id not in metrics:
            metrics[user_id] = {
                "start_time": time.time(),
                "messages_count": 0,
                "first_message_time": None
            }
        
        metrics[user_id]["messages_count"] += 1
        if metrics[user_id]["first_message_time"] is None:
            metrics[user_id]["first_message_time"] = time.time()
        
        # Создаем модель с поддержкой изображений
        if user_id not in chats:
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=SYSTEM_PROMPT
            )
            chats[user_id] = model.start_chat(history=[])
        
        chat = chats[user_id]
        
        # Загружаем изображение
        image = Image.open(image_path)
        
        # Отправляем сообщение с изображением
        start_request = time.time()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        
        response = await loop.run_in_executor(
            None, 
            lambda: chat.send_message([user_text, image])
        )
        request_time = time.time() - start_request
        
        ai_text = response.text
        
        # Проверяем JSON ответ
        clean_text = ai_text.replace("```json", "").replace("```", "").strip()
        
        try:
            if "{" in clean_text and "}" in clean_text:
                data = json.loads(clean_text)
                if data.get("status") == "completed":
                    total_time = time.time() - metrics[user_id]["first_message_time"]
                    data["metrics"] = {
                        "total_time_seconds": round(total_time, 2),
                        "total_time_minutes": round(total_time / 60, 2),
                        "messages_count": metrics[user_id]["messages_count"],
                        "last_request_time": round(request_time, 2)
                    }
                    if user_id in metrics:
                        del metrics[user_id]
                    return {"type": "final", "data": data}
        except json.JSONDecodeError:
            pass
        
        return {"type": "text", "text": ai_text}
    except Exception as e:
        return {"type": "error", "text": str(e)}

def generate_diagram_link(mermaid_code: str) -> str:
    """Превращает код диаграммы в картинку через сервис mermaid.ink"""
    graphbytes = mermaid_code.encode("utf8")
    base64_bytes = base64.b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    return "https://mermaid.ink/img/" + base64_string

