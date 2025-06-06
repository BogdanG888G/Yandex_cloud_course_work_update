import os
from dotenv import load_dotenv
load_dotenv()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import aiohttp

user_states = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_states[update.effective_user.id] = {"step": 0, "params": []}
    await update.message.reply_text(
        "👋 *Привет! Я — WB Парсер Бот.*\n\n"
        "Я помогу найти товары на Wildberries по:\n"
        "▪️ Категории\n▪️ Цене\n▪️ Скидке\n\n"
        "🔍 Введи ссылку на категорию WB, с которой начнём анализ.\n"
        "_Пример: https://www.wildberries.ru/catalog/elektronika/igry-i-razvlecheniya/aksessuary/garnitury_",
        parse_mode="Markdown"
    )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = user_states.get(user_id, {"step": 0, "params": []})

    try:
        if state["step"] == 0:  # URL
            if "wildberries.ru/catalog" not in text:
                await update.message.reply_text("❌ Неверная ссылка WB. Попробуйте ещё раз.")
                return
            state["params"].append(text)
            state["step"] = 1
            user_states[user_id] = state
            await update.message.reply_text("💰 Введите *нижнюю* границу цены (только число):", parse_mode="Markdown")

        elif state["step"] == 1:  # Нижняя цена
            if not text.isdigit():
                await update.message.reply_text("❌ Введите корректное число!")
                return
            state["params"].append(int(text))
            state["step"] = 2
            user_states[user_id] = state
            await update.message.reply_text("💰 Введите *верхнюю* границу цены (только число):", parse_mode="Markdown")

        elif state["step"] == 2:  # Верхняя цена
            if not text.isdigit():
                await update.message.reply_text("❌ Введите корректное число!")
                return
            state["params"].append(int(text))
            state["step"] = 3
            user_states[user_id] = state
            await update.message.reply_text("🔻 Введите минимальную скидку (0-100):")

        elif state["step"] == 3:  # Скидка
            if not text.isdigit() or not (0 <= int(text) <= 100):
                await update.message.reply_text("❌ Скидка должна быть от 0 до 100%! Попробуйте снова:")
                return

            state["params"].append(int(text))
            user_states[user_id] = state
            url, low, high, discount = state["params"]

            await update.message.reply_text("⏳ *Запускаю парсер...*", parse_mode="Markdown")

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        "http://parser_api:8050/parse",
                        json={"url": url, "low": low, "high": high, "discount": discount}
                    ) as resp:
                        data = await resp.json()
                        if data.get("status") == "ok":
                            await update.message.reply_text(
                                "✅ *Парсер успешно завершил работу!*\n\n"
                                "📊 Результаты доступны по ссылке:\n"
                                "[Открыть дашборд](http://158.160.124.117:8088/superset/dashboard/p/P4WnyelQorV/)",
                                parse_mode="Markdown"
                            )
                        else:
                            await update.message.reply_text(f"⚠️ Ошибка парсера: {data.get('detail')}")
                except Exception as e:
                    await update.message.reply_text(f"🚫 Ошибка при вызове парсера: {str(e)}")

            # Сброс состояния
            user_states[user_id] = {"step": 0, "params": []}
            await update.message.reply_text(
                "🔁 *Хочешь начать заново?*\nВведи новую ссылку на категорию WB:",
                parse_mode="Markdown"
            )

    except Exception as e:
        await update.message.reply_text(f"❗ Произошла ошибка: {str(e)}")

# Точка входа
if __name__ == '__main__':
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN не найден в .env!")
    else:
        print(f"✅ BOT_TOKEN загружен: {token[:10]}...")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
