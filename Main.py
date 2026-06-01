import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "8762560526:AAE0TENxNdrtw_0IYCHGYPn3WbQ-0NUUPnM"

WORDS = [
    "Ядерная электростанция",
    "Унитаз",
    "Университет",
    "Школа",
    "Президент",
    "Премьер-министр",
    "Франция",
    "Червь",
]

def get_main_menu():
    keyboard = [[InlineKeyboardButton("🕵️ Шпион", callback_data="open_spy")]]
    return InlineKeyboardMarkup(keyboard)

def get_player_count_keyboard():
    buttons = []
    row = []
    for i in range(3, 11):
        row.append(InlineKeyboardButton(str(i), callback_data=f"players_{i}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)

def get_spy_count_keyboard(players: int):
    max_spies = players // 2
    buttons = []
    row = []
    for i in range(1, max_spies + 1):
        row.append(InlineKeyboardButton(str(i), callback_data=f"spies_{i}"))
    buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="back_players")])
    return InlineKeyboardMarkup(buttons)

def get_view_word_keyboard(player_index: int, total: int):
    buttons = [[InlineKeyboardButton("👁 Посмотреть слово", callback_data=f"view_word_{player_index}")]]
    return InlineKeyboardMarkup(buttons)

def get_close_word_keyboard(player_index: int):
    buttons = [[InlineKeyboardButton("🙈 Закрыть слово", callback_data=f"close_word_{player_index}")]]
    return InlineKeyboardMarkup(buttons)

def get_start_game_keyboard():
    buttons = [[InlineKeyboardButton("🚀 Начать игру", callback_data="start_game")]]
    return InlineKeyboardMarkup(buttons)

def get_end_game_keyboard():
    buttons = [[InlineKeyboardButton("🏁 Закончить игру", callback_data="end_game")]]
    return InlineKeyboardMarkup(buttons)

def get_postgame_keyboard():
    buttons = [
        [InlineKeyboardButton("🔄 Сыграть ещё раз", callback_data="play_again")],
        [InlineKeyboardButton("🏠 Вернуться в меню", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(buttons)

def build_game_state(players: int, spies: int):
    word = random.choice(WORDS)
    roles = ["🕵️ Ты шпион!"] * spies + [f"📍 Твоё слово:\n<b>{word}</b>"] * (players - spies)
    random.shuffle(roles)
    return {
        "players": players,
        "spies": spies,
        "word": word,
        "roles": roles,
        "current_player": 0,
        "viewed": 0,
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Добро пожаловать в <b>Мини-игры бот</b>!\nВыбери игру:",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

async def spion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🕵️ <b>Игра: Шпион</b>\n\nВыбери количество игроков:",
        parse_mode="HTML",
        reply_markup=get_player_count_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "open_spy" or data == "back_players":
        if data == "back_players":
            context.user_data.pop("players", None)
        await query.edit_message_text(
            "🕵️ <b>Игра: Шпион</b>\n\nВыбери количество игроков:",
            parse_mode="HTML",
            reply_markup=get_player_count_keyboard()
        )

    elif data == "back_main":
        context.user_data.clear()
        await query.edit_message_text(
            "👋 Добро пожаловать в <b>Мини-игры бот</b>!\nВыбери игру:",
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )

    elif data.startswith("players_"):
        players = int(data.split("_")[1])
        context.user_data["players"] = players
        await query.edit_message_text(
            f"👥 Игроков: <b>{players}</b>\n\nВыбери количество шпионов:",
            parse_mode="HTML",
            reply_markup=get_spy_count_keyboard(players)
        )

    elif data.startswith("spies_"):
        spies = int(data.split("_")[1])
        players = context.user_data.get("players", 3)
        context.user_data["spies"] = spies
        context.user_data["game"] = build_game_state(players, spies)
        await query.edit_message_text(
            f"✅ Игроков: <b>{players}</b> | Шпионов: <b>{spies}</b>\n\n"
            f"<b>Игрок 1</b>, нажми кнопку чтобы посмотреть своё слово.\nПосле просмотра передай телефон следующему.",
            parse_mode="HTML",
            reply_markup=get_view_word_keyboard(0, players)
        )

    elif data.startswith("view_word_"):
        player_index = int(data.split("_")[2])
        game = context.user_data.get("game")
        if not game:
            return
        role = game["roles"][player_index]
        await query.edit_message_text(
            f"<b>Игрок {player_index + 1}</b>\n\n{role}\n\n⬇️ Посмотрел? Нажми закрыть и передай телефон.",
            parse_mode="HTML",
            reply_markup=get_close_word_keyboard(player_index)
        )

    elif data.startswith("close_word_"):
        player_index = int(data.split("_")[2])
        game = context.user_data.get("game")
        if not game:
            return
        next_index = player_index + 1
        total = game["players"]

        if next_index < total:
            await query.edit_message_text(
                f"✅ Игроков посмотрело: <b>{next_index}/{total}</b>\n\n"
                f"<b>Игрок {next_index + 1}</b>, нажми кнопку чтобы посмотреть своё слово.",
                parse_mode="HTML",
                reply_markup=get_view_word_keyboard(next_index, total)
            )
        else:
            await query.edit_message_text(
                f"✅ Все <b>{total}</b> игроков посмотрели своё слово!\n\n"
                "Когда будете готовы — начинайте игру.\nЗадавайте вопросы и ищите шпиона! 🕵️",
                parse_mode="HTML",
                reply_markup=get_start_game_keyboard()
            )

    elif data == "start_game":
        await query.edit_message_text(
            "🎮 <b>Игра началась!</b>\n\nЗадавайте друг другу вопросы по локации.\nШпион пытается не раскрыться!\n\nКогда найдёте шпиона — нажмите кнопку.",
            parse_mode="HTML",
            reply_markup=get_end_game_keyboard()
        )

    elif data == "end_game":
        game = context.user_data.get("game")
        if not game:
            return
        word = game["word"]
        spy_indices = [i + 1 for i, r in enumerate(game["roles"]) if "шпион" in r]
        spy_list = ", ".join([f"Игрок {n}" for n in spy_indices])
        await query.edit_message_text(
            f"🏁 <b>Игра окончена!</b>\n\n"
            f"🕵️ Шпион(ы): <b>{spy_list}</b>\n"
            f"📍 Слово было: <b>{word}</b>",
            parse_mode="HTML",
            reply_markup=get_postgame_keyboard()
        )

    elif data == "play_again":
        players = context.user_data.get("players", 3)
        spies = context.user_data.get("spies", 1)
        context.user_data["game"] = build_game_state(players, spies)
        await query.edit_message_text(
            f"🔄 Новая игра!\nИгроков: <b>{players}</b> | Шпионов: <b>{spies}</b>\n\n"
            f"<b>Игрок 1</b>, нажми кнопку чтобы посмотреть своё слово.",
            parse_mode="HTML",
            reply_markup=get_view_word_keyboard(0, players)
        )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text == "spion":
        context.user_data.clear()
        await update.message.reply_text(
            "🕵️ <b>Игра: Шпион</b>\n\nВыбери количество игроков:",
            parse_mode="HTML",
            reply_markup=get_player_count_keyboard()
        )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("spion", spion_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
