from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import requests

TELEGRAM_TOKEN = ''
DEEPSEEK_API_KEY = ''

STYLE_PRESETS = {
    "official": "улучшай текст в официальном деловом стиле",
    "casual": "улучшай текст в простом и понятном разговорном стиле",
    "emotional": "улучшай текст, делая его более ярким и эмоциональным",
    "neutral": "улучшай текст грамотно, но без изменения общего тона"
}

user_selected_style = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я улучшаю текст. Чтобы начать, используй команду /improve"
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Доступные команды:\n"
        "/improve — выбрать стиль улучшения текста\n"
        "/style — сменить стиль\n"
        "/reset — сбросить выбранный стиль\n"
        "/help — помощь"
    )

# Команда /improve и /style
async def choose_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Официальный", callback_data='style_official')],
        [InlineKeyboardButton("Разговорный", callback_data='style_casual')],
        [InlineKeyboardButton("Эмоциональный", callback_data='style_emotional')],
        [InlineKeyboardButton("Нейтральный", callback_data='style_neutral')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери стиль для улучшения текста:", reply_markup=reply_markup)

# Обработка выбора стиля
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    style_key = query.data.replace("style_", "")
    chat_id = query.message.chat_id
    user_selected_style[chat_id] = style_key
    await query.message.reply_text(f"✅ Стиль выбран: {style_key}. Теперь отправь текст, который нужно улучшить.")

# Команда /reset
async def reset_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_selected_style.pop(chat_id, None)
    await update.message.reply_text("Стиль сброшен. Введите /improve, чтобы выбрать заново.")

# Обработка текста
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_text = update.message.text
    style = user_selected_style.get(chat_id)

    if not style:
        await update.message.reply_text("Сначала выбери стиль командой /improve")
        return

    improved = await improve_text_variants(user_text, style, n=3)
    await update.message.reply_text(f"✨ Вот улучшенные варианты:\n\n{improved}")

# Запрос к DeepSeek
async def improve_text_variants(user_text: str, style: str, n=3) -> str:
    style_instruction = STYLE_PRESETS.get(style.lower())
    if not style_instruction:
        return f"❌ Неизвестный стиль: {style}"

    system_prompt = (
        f"Ты помощник, который помогает улучшать текст. "
        f"Пользователь даёт текст, а ты возвращаешь {n} улучшенных вариантов, "
        f"в заданном стиле. Вот стиль: {style_instruction}. "
        f"Не объясняй. Просто выдай {n} вариантов, с нумерацией."
    )

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.8
    }

    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Ошибка при обращении к DeepSeek: {e}"

# Инициализация
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("improve", choose_style))
app.add_handler(CommandHandler("style", choose_style))
app.add_handler(CommandHandler("reset", reset_style))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("Бот запущен с командами")
app.run_polling()
