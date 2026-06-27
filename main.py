import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Telegram Mini App Proxy API")

# Разрешаем CORS для твоего мини-аппа
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://5bc3a350.krutoyrentnomerov.pages.dev",
        "https://krutoyrentnomerov.pages.dev",
        "*"  # Для теста, потом можно убрать
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = os.getenv("API_URL", "https://extether.duckdns.org")
API_TOKEN = os.getenv("API_TOKEN")

# ============================================================
#  МОДЕЛИ
# ============================================================
class OrderRequest(BaseModel):
    number: str
    days: int = 1

class NumberRequest(BaseModel):
    number: str

# ============================================================
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
async def api_request(endpoint: str, method: str = "GET", body: dict = None):
    """Универсальная функция для запросов к API"""
    url = f"{API_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=body)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"API error: {response.text}"
            )
        
        return response.json()

# ============================================================
#  ЭНДПОИНТЫ
# ============================================================

@app.get("/")
async def root():
    return {"message": "Telegram Mini App Proxy API", "status": "running"}

@app.get("/api/numbers")
async def get_numbers():
    """Получить список всех номеров"""
    try:
        data = await api_request("/numbers")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/number/{number}")
async def get_number(number: str):
    """Получить информацию о конкретном номере"""
    try:
        data = await api_request(f"/number/{number}")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order")
async def create_order(order: OrderRequest):
    """Создать заказ (арендовать номер)"""
    try:
        data = await api_request(
            "/order",
            method="POST",
            body={"number": order.number, "days": order.days}
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/number/{number}/codes")
async def get_codes(number: str):
    """Получить коды для номера"""
    try:
        data = await api_request(f"/number/{number}/codes", method="POST")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/number/{number}/terminate")
async def terminate_session(number: str):
    """Завершить сессию (освободить номер)"""
    try:
        data = await api_request(f"/number/{number}/terminate-sessions", method="POST")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/me")
async def get_me():
    """Получить информацию о пользователе"""
    try:
        data = await api_request("/me")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
#  ЗАПУСК
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)