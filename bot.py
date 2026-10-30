import httpx
import os
import asyncio
from video_maker import make_video
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

DATA_FILE = "creator_data.json"
BNBIT_URL = "https://bnbit.com/"


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def user_record(user_id):
    data = load_data()
    key = str(user_id)
    if key not in data:
        data[key] = {"income": [], "expenses": []}
        save_data(data)
    return data, data[key]


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Video Ideas", callback_data="ideas")],
        [InlineKeyboardButton("✍️ Caption Maker", callback_data="caption")],
        [InlineKeyboardButton("🎞️ Video Script", callback_data="script")],
        [InlineKeyboardButton("🎥 Create Video", callback_data="video")],
        [InlineKeyboardButton("🎙️ ወንድ ድምፅ", callback_data="voice_male"),
         InlineKeyboardButton("🎙️ ሴት ድምፅ", callback_data="voice_female")],
        [InlineKeyboardButton("📅 Weekly Planner", callback_data="planner")],
        [InlineKeyboardButton("💰 Income Tracker", callback_data="tracker")],
        [InlineKeyboardButton("🌐 Bnbit Website", url=BNBIT_URL)],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("mode", None)
    await update.effective_message.reply_text(
        "🤖 KBReal Creator Helper\n\n"
        "የይዘት ሀሳብ፣ የፖስት ጽሑፍ፣ የቪዲዮ ስክሪፕት "
        "እና የገቢ/ወጪ መዝገብ ለማዘጋጀት ከታች ምረጥ።\n\n"
        "⚠️ ይህ ቦት ገቢ አያረጋግጥም እና ከBnbit ጋር በቀጥታ አልተገናኘም።",
        reply_markup=main_keyboard(),
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query is None:
        return

    try:
        await query.answer()
    except Exception as e:
        print("Callback answer error:", repr(e), flush=True)

    action = query.data
    print("BUTTON CLICKED:", action, flush=True)

    if action == "voice_male":
        context.user_data["voice"] = "am-ET-AmehaNeural"
        await query.message.reply_text("✅ የወንድ ድምፅ ተመርጧል።", reply_markup=main_keyboard())
        return

    if action == "voice_female":
        context.user_data["voice"] = "am-ET-MekdesNeural"
        await query.message.reply_text("✅ የሴት ድምፅ ተመርጧል።", reply_markup=main_keyboard())
        return

    if action == "ideas":
        ideas = [
            "🇪🇹 የኢትዮጵያ ባህል በ30 ሰከንድ",
            "💡 3 ጠቃሚ የስልክ ምክሮች",
            "😂 ኦሪጅናል አስቂኝ ታሪክ",
            "📚 በአንድ ደቂቃ አዲስ ነገር አስተምር",
            "🌱 ከትንሽ ነገር ትልቅ ለውጥ የሚያመጣ ታሪክ",
            "🍲 የአካባቢ ምግብ አዘገጃጀት",
            "🎨 በስልክ የሚሰራ ቀላል ዲዛይን",
        ]
        random.shuffle(ideas)
        text = "🎬 የቪዲዮ ሀሳቦች\n\n" + "\n".join(
            f"{i+1}. {idea}" for i, idea in enumerate(ideas[:5])
        )
        text += "\n\nአንዱን ምረጥና በራስህ ኦሪጅናል ቪዲዮ አዘጋጅ።"

    elif action == "caption":
        context.user_data["mode"] = "caption"
        text = "✍️ ስለ ምን እንደምትፖስት ጻፍ።\nምሳሌ፦ የኢትዮጵያ ባህል"

    elif action == "script":
        context.user_data["mode"] = "script"
        text = "🎞️ የቪዲዮህን ርዕስ ጻፍ።\nምሳሌ፦ የስልክ ጠቃሚ ምክሮች"

    elif action == "video":
        context.user_data["mode"] = "video"
        text = (
            "🎥 የቪዲዮ ርዕስህን በእንግሊዝኛ ጻፍ።\\n"
            "ምሳሌ፦ My First Video\\n\\n"
            "ቦቱ ቀጥ ያለ MP4 ቪዲዮ ይፈጥርልሃል።"
        )

    elif action == "planner":
        text = (
            "📅 የ7 ቀን የይዘት እቅድ\n\n"
            "ሰኞ — 🎓 የማስተማሪያ ቪዲዮ\n"
            "ማክሰኞ — 🇪🇹 የባህል ይዘት\n"
            "ረቡዕ — 💡 ጠቃሚ ምክር\n"
            "ሐሙስ — 😂 ኦሪጅናል አስቂኝ ቪዲዮ\n"
            "ዓርብ — 📖 አጭር ታሪክ\n"
            "ቅዳሜ — 🎬 ከፍተኛ ጥረት የሚፈልግ ፕሮጀክት\n"
            "እሁድ — 📊 ውጤትህን ገምግምና ቀጣዩን ሳምንት አቅድ\n\n"
            "የሌሎችን ቪዲዮ በቀጥታ ከመቅዳት ይልቅ የራስህን ስራ ፍጠር።"
        )

    elif action == "tracker":
        context.user_data.pop("mode", None)
        text = (
            "💰 የገቢና ወጪ መዝገብ\n\n"
            "ገቢ ለመመዝገብ፦\n"
            "/income 100 የተቀበልከው መጠን\n\n"
            "ወጪ ለመመዝገብ፦\n"
            "/expense 20 የወጣው መጠን\n\n"
            "ቀሪ ለማየት፦ /balance\n"
            "የመጨረሻ መዝገቦች፦ /history\n\n"
            "መጠኖቹን በራስህ በትክክል አስገባ።"
        )
    else:
        text = "ከታች ያሉትን አማራጮች ተጠቀም።"

    await query.message.reply_text(text, reply_markup=main_keyboard())


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.pop("mode", None)
    topic = (update.effective_message.text or "").strip()
    topic = topic.replace("ብለህ ላክ።", "").strip()

    if not topic:
        return

    if mode == "video":
        message = await update.effective_message.reply_text(
            "⏳ ቪዲዮውን እያዘጋጀሁ ነው። ትንሽ ጠብቅ..."
        )
        try:
            video_path = await asyncio.to_thread(make_video, topic, context.user_data.get("voice", "am-ET-MekdesNeural"))
            with open(video_path, "rb") as video_file:
                await update.effective_message.reply_video(
                    video=video_file,
                    caption=f"🎥 KBReal Creator Video\\n📝 {topic[:200]}"
                )
            await message.delete()
        except Exception as e:
            import traceback
            print("Video generation/send error:", repr(e))
            traceback.print_exc()
            await message.edit_text(
                "❌ ቪዲዮውን ማዘጋጀት አልተሳካም። "
                "FFmpeg እና video_maker.py እንደሚሰሩ እንፈትሽ።"
            )
        return

    if mode == "caption":
        captions = [
            (
                f"🔥 {topic} — ይህ ርዕስ ብዙ የሚነገርለት ነገር አለው!\n\n"
                "✨ አዲስ ሀሳብ፣ አዲስ እይታ፣ አዲስ ተሞክሮ።\n"
                "💬 አንተስ ምን ታስባለህ? አስተያየትህን አጋራ።\n\n"
                "#Ethiopia #KBReal #Creator"
            ),
            (
                f"🇪🇹 የዛሬው ርዕሳችን፦ {topic}\n\n"
                "ባህላችንን፣ ሀሳባችንንና ጥሩ ተሞክሮዎቻችንን እናጋራ።\n"
                "❤️ ይህን ይዘት ለጓደኞችህ አጋራ።\n\n"
                "#EthiopianCulture #Ethiopia #KBReal"
            ),
            (
                f"💡 ስለ {topic} አንድ ጥያቄ!\n\n"
                "ይህ ርዕስ ለእኛ ምን ትርጉም አለው?\n"
                "👇 የአንተን ሀሳብ በአስተያየት አጋራ።\n\n"
                "#Discussion #Ethiopia #OriginalContent"
            ),
        ]
        text = "✍️ 3 የCaption አማራጮች\n\n" + "\n\n━━━━━━━━━━━━\n\n".join(captions)

    elif mode == "script":
        text = (
            f"🎞️ የቪዲዮ ስክሪፕት\\n"
            f"ርዕስ፦ {topic}\\n\\n"
            "🎬 መግቢያ — ተመልካችን የሚስብ ጥያቄ ጠይቅ።\\n"
            f"🎥 ዋና ሀሳብ — {topic}\\n"
            "✅ መደምደሚያ — ጠቃሚ ማጠቃለያ ስጥ።\\n\\n"
            "⏳ አሁን MP4 ቪዲዮ እያዘጋጀሁ ነው..."
        )
        await update.effective_message.reply_text(text)

        try:
            video_path = await asyncio.to_thread(make_video, topic, context.user_data.get("voice", "am-ET-MekdesNeural"))
            with open(video_path, "rb") as video_file:
                await update.effective_message.reply_video(
                    video=video_file,
                    caption=f"🎥 KBReal Creator Video\\n📝 {topic[:200]}"
                )
        except Exception as e:
            print("Video generation error:", repr(e))
            await update.effective_message.reply_text(
                "❌ ቪዲዮውን መፍጠር አልተሳካም። የTermux ስህተቱን ላክልኝ።"
            )
        return

    else:
        await update.effective_message.reply_text(
            "እባክህ /start ተጫንና ከምናሌው አንዱን ምረጥ።"
        )
        return

    await update.effective_message.reply_text(
        text, reply_markup=main_keyboard()
    )


async def record_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.effective_message.text.split(maxsplit=1)
    if len(command) < 2:
        await update.effective_message.reply_text(
            "መጠኑን አስገባ። ምሳሌ፦ /income 100"
        )
        return

    try:
        amount = float(command[1].split()[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "ትክክለኛ ቁጥር አስገባ። ምሳሌ፦ /income 100"
        )
        return

    data, record = user_record(update.effective_user.id)
    entry = {
        "amount": amount,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "note": " ".join(command[1].split()[1:]),
    }

    if command[0].startswith("/income"):
        record["income"].append(entry)
        label = "ገቢ"
    else:
        record["expenses"].append(entry)
        label = "ወጪ"

    data[str(update.effective_user.id)] = record
    save_data(data)

    await update.effective_message.reply_text(
        f"✅ {label} ተመዝግቧል።\nመጠን፦ {amount:g}\n\n/balance በመጻፍ ቀሪህን አይ።"
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, record = user_record(update.effective_user.id)
    income = sum(x["amount"] for x in record["income"])
    expenses = sum(x["amount"] for x in record["expenses"])
    await update.effective_message.reply_text(
        f"📊 የመዝገብ ማጠቃለያ\n\n"
        f"💵 ጠቅላላ ገቢ፦ {income:g}\n"
        f"💸 ጠቅላላ ወጪ፦ {expenses:g}\n"
        f"🧮 ቀሪ፦ {income - expenses:g}\n\n"
        "ይህ በአንተ ያስገባኸው መረጃ ላይ ብቻ የተመሰረተ ነው።"
    )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, record = user_record(update.effective_user.id)
    entries = [
        ("➕ ገቢ", x) for x in record["income"]
    ] + [
        ("➖ ወጪ", x) for x in record["expenses"]
    ]
    entries.sort(key=lambda pair: pair[1]["date"], reverse=True)
    if not entries:
        await update.effective_message.reply_text(
            "ምንም መዝገብ የለም። /income 100 ወይም /expense 20 በመጻፍ ጀምር።"
        )
        return

    lines = ["📒 የመጨረሻ 10 መዝገቦች\n"]
    for label, entry in entries[:10]:
        lines.append(
            f"{label}: {entry['amount']:g} — {entry['date']}"
        )
    await update.effective_message.reply_text("\n".join(lines))


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, record = user_record(update.effective_user.id)
    income = sum(x["amount"] for x in record["income"])
    expenses = sum(x["amount"] for x in record["expenses"])
    balance_amount = income - expenses
    total_records = len(record["income"]) + len(record["expenses"])

    await update.effective_message.reply_text(
        "📊 KBReal Creator Dashboard\\n\\n"
        f"💵 ጠቅላላ ገቢ፦ {income:g}\\n"
        f"💸 ጠቅላላ ወጪ፦ {expenses:g}\\n"
        f"🧮 ቀሪ ሂሳብ፦ {balance_amount:g}\\n"
        f"📒 የመዝገብ ብዛት፦ {total_records}\\n\\n"
        "ዝርዝር ለማየት /history ተጠቀም።"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "/start — ዋና ምናሌ\n"
        "/income 100 — ገቢ መመዝገብ\n"
        "/expense 20 — ወጪ መመዝገብ\n"
        "/balance — ቀሪ ማየት\n"
        "/history — መዝገቦች ማየት\n"
        "/help — እገዛ"
    )


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERROR: BOT_TOKEN አልተገኘም።")
        print("በTermux ውስጥ export BOT_TOKEN='የቦትህን_ቶከን' አስገባ።")
        return

    request = HTTPXRequest(
        connection_pool_size=1,
        connect_timeout=60,
        read_timeout=180,
        write_timeout=180,
        pool_timeout=60,
        httpx_kwargs={"trust_env": False, "transport": httpx.AsyncHTTPTransport(retries=5)},
    )
    updates_request = HTTPXRequest(
        connection_pool_size=1,
        connect_timeout=60,
        read_timeout=180,
        write_timeout=180,
        pool_timeout=60,
        httpx_kwargs={"trust_env": False, "transport": httpx.AsyncHTTPTransport(retries=5)},
    )
    app = (
        Application.builder()
        .token(token)
        .request(request)
        .get_updates_request(updates_request)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("income", record_amount))
    app.add_handler(CommandHandler("expense", record_amount))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("KBReal Creator Helper is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
