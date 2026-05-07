import os
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= 🔧 [ কনফিগারেশন ] =================
BOT_TOKEN = "8260254278:AAE0ZTPrPVQExDHS0VWhA7T8f_Bp8S1gYiI"

# ================= 🚀 [ স্টার্ট কমান্ড ] =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ *Duplicate Remover Bot Active!*\n\n"
        "📂 Send me a `.csv` or `.xlsx` file.\n"
        "I will remove all duplicate rows and send you:\n"
        "1️⃣ `Unique_Data.xlsx` (only unique records)\n"
        "2️⃣ `Duplicate_Data.xlsx` (removed duplicates)\n\n"
        "⚠️ The bot checks ALL columns for duplicates.\n"
        "💡 Powered by MAX FUTURE",
        parse_mode="Markdown"
    )

# ================= 📂 [ ফাইল হ্যান্ডলার ] =================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = update.message.document.file_name
    input_file = f"input_{file_name}"
    unique_file = "Unique_Data.xlsx"
    duplicate_file = "Duplicate_Data.xlsx"

    try:
        file = await context.bot.get_file(update.message.document.file_id)
        await file.download_to_drive(input_file)

        await update.message.reply_text("⏳ Processing file, please wait...")

        if file_name.lower().endswith('.csv'):
            try:
                df = pd.read_csv(input_file, encoding='utf-8')
            except:
                df = pd.read_csv(input_file, encoding='latin1')
        else:
            df = pd.read_excel(input_file)

        if df.empty:
            await update.message.reply_text("❌ The file is empty!")
            return

        duplicate_mask = df.duplicated(keep='first')
        unique_df = df[~duplicate_mask]
        duplicate_df = df[duplicate_mask]

        unique_df.to_excel(unique_file, index=False)
        duplicate_df.to_excel(duplicate_file, index=False)

        with open(unique_file, 'rb') as f:
            await update.message.reply_document(
                document=f,
                caption=f"✅ *Unique Data* (Total: {len(unique_df)} records)"
            )

        if len(duplicate_df) > 0:
            with open(duplicate_file, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    caption=f"🗑️ *Duplicate Data* (Total: {len(duplicate_df)} records removed)"
                )
        else:
            await update.message.reply_text("✅ No duplicates found! All data is unique.")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

    finally:
        for f in [input_file, unique_file, duplicate_file]:
            if os.path.exists(f):
                os.remove(f)

# ================= 🔄 [ মেইন ] =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("=" * 40)
    print("✅ Duplicate Remover Bot Started!")
    print("💡 Send /start on Telegram to begin")
    print("=" * 40)
    
    app.run_polling()

if __name__ == '__main__':
    main()
