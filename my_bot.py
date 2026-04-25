import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from aiohttp import web
import asyncio

# ==================== ВСТАВЬ СВОИ КЛЮЧИ ====================
TELEGRAM_TOKEN = "8172085369:AAFBMaxYmrTYp0I97ihndQhN3sjqwTCKc6s"
DEEPSEEK_API_KEY = "sk-9929a65b938d4cb49d43888c8777f93d"
# ===========================================================

client = openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

async def generate_answer(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты — вежливый и опытный помощник электрика. Отвечаешь по делу, можешь дать предварительную консультацию, узнаешь проблему и сообщаешь, что мастер скоро свяжется."},
                {"role": "user", "content": user_message}
            ],
            stream=False,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка от DeepSeek: {e}")
        return "Извините, я немного задумался. Повторите, пожалуйста, ваш вопрос."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Я автоматический помощник электрика. Опишите вашу проблему, и я постараюсь помочь.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action(action="typing")
    answer = await generate_answer(user_text)
    await update.message.reply_text(answer)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я могу ответить на вопросы по электрике. Просто опишите проблему.")

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    # Инициализация приложения
    await app.initialize()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    PORT = int(os.environ.get("PORT", 10000))
    WEBHOOK_URL = "https://" + os.environ.get("RENDER_EXTERNAL_HOSTNAME", "") + "/webhook"

    if WEBHOOK_URL != "/webhook":
        await app.bot.set_webhook(WEBHOOK_URL)
        print(f"Webhook set to {WEBHOOK_URL}")
    else:
        print("!!! RENDER_EXTERNAL_HOSTNAME not set, cannot set webhook !!!")

    async def webhook(request):
        if request.method == "POST":
            data = await request.json()
            await app.process_update(Update.de_json(data, app.bot))
            return web.Response()
        return web.Response(text="OK")

    app_webhook = web.Application()
    app_webhook.router.add_post("/webhook", webhook)
    runner = web.AppRunner(app_webhook)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Сервер запущен на порту {PORT}...")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
