import os
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

app = FastAPI(title="Telegram Mini App + Bot API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = os.getenv("API_URL", "https://extether.duckdns.org")
API_TOKEN = os.getenv("API_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ============================================================
#  ФУНКЦИИ ДЛЯ API
# ============================================================
async def api_request(endpoint: str, method: str = "GET", body: dict = None):
    url = f"{API_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=body)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

# ============================================================
#  КОМАНДЫ БОТА
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📱 Арендовать номер", url="https://t.me/Anonnumberrent_bot/rent")],
        [InlineKeyboardButton("📢 Наш телеграм канал", url="https://t.me/anonymenumberrent")],
        [InlineKeyboardButton("🆘 Тех поддержка", url="https://t.me/anonrentsupport_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Добро пожаловать в сервис аренды анонимных номеров!\n"
        "Здесь хранится ключ к вашей анонимности.\n\n"
        "Что вы можете сделать:\n"
        "➡️ Арендовать номер - получите номер для регистрации или смены номера.\n\n"
        "📌 Для навигации используйте меню ниже.",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📱 Арендовать номер", url="https://t.me/Anonnumberrent_bot/rent")],
        [InlineKeyboardButton("📢 Наш телеграм канал", url="https://t.me/anonymenumberrent")],
        [InlineKeyboardButton("🆘 Тех поддержка", url="https://t.me/anonrentsupport_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📖 Доступные команды:\n\n"
        "/start — Главное меню\n"
        "/help — Помощь\n"
        "/numbers — Список свободных номеров\n\n"
        "Или используйте кнопки ниже:",
        reply_markup=reply_markup
    )

async def numbers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Загружаю список номеров...")
    
    try:
        data = await api_request("/numbers")
        if data and data.get("available"):
            text = "📞 Свободные номера:\n\n"
            for item in data["available"]:
                price = item.get("price", 0)
                text += f"➕ {item['number']} — {price} $\n"
            
            if data.get("rented"):
                text += f"\n🔴 В аренде: {len(data['rented'])} номеров"
            
            keyboard = [
                [InlineKeyboardButton("📱 Арендовать номер", url="https://t.me/Anonnumberrent_bot/rent")],
                [InlineKeyboardButton("🆘 Тех поддержка", url="https://t.me/anonrentsupport_bot")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text("❌ Нет свободных номеров.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка загрузки: {str(e)}")

# ============================================================
#  ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================================
bot_app = Application.builder().token(BOT_TOKEN).build()

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(CommandHandler("numbers", numbers_command))

# ============================================================
#  СОБЫТИЕ ПРИ ЗАПУСКЕ - ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================================
@app.on_event("startup")
async def startup_event():
    """Инициализируем бота при старте сервера"""
    await bot_app.initialize()
    print("✅ Бот инициализирован")

# ============================================================
#  ВЕБХУК
# ============================================================
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/webhook")
async def webhook_get():
    return {"status": "webhook endpoint"}

# ============================================================
#  ЭНДПОИНТЫ ДЛЯ МИНИ-АППА
# ============================================================
@app.get("/")
async def root():
    return {"message": "Telegram Mini App + Bot API", "status": "running"}

@app.get("/api/numbers")
async def get_numbers():
    try:
        data = await api_request("/numbers")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order")
async def create_order(order: dict):
    try:
        data = await api_request("/order", method="POST", body=order)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/number/{number}/terminate")
async def terminate_session(number: str):
    try:
        data = await api_request(f"/number/{number}/terminate-sessions", method="POST")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
#  ЗАПУСК
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)