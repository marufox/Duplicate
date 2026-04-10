import pandas as pd
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# আপনার টেলিগ্রাম বট টোকেন
TOKEN = '8260254278:AAE0ZTPrPVQExDHS0VWhA7T8f_Bp8S1gYiI'

# আপনার চাহিদা অনুযায়ী কলামের নাম সেট করা হলো
CHECK_COLUMNS = ['user', 'pass'] 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "বট সক্রিয় আছে! ✅\n\nআপনার .csv বা .xlsx ফাইলটি পাঠান। আমি 'user' এবং 'pass' কলামের ভিত্তিতে ডুপ্লিকেট আলাদা করে দেব।"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = update.message.document.file_name
    input_file = f"input_{file_name}"
    clean_filename = "Clean_Data.xlsx"
    removed_filename = "Removed_Duplicates.xlsx"

    try:
        # ফাইল ডাউনলোড
        file = await context.bot.get_file(update.message.document.file_id)
        await file.download_to_drive(input_file)
        
        await update.message.reply_text("ফাইল প্রসেস করা হচ্ছে, দয়া করে অপেক্ষা করুন...")

        # ডাটা লোড করা
        if file_name.lower().endswith('.csv'):
            try:
                df = pd.read_csv(input_file, encoding='utf-8')
            except:
                df = pd.read_csv(input_file, encoding='latin1')
        else:
            df = pd.read_excel(input_file)

        # কলামের নামগুলো পরিষ্কার করা (Spaces মুছে ছোট হাতের করা)
        df.columns = [str(col).strip().lower() for col in df.columns]

        # চেক করা যে 'user' এবং 'pass' কলাম আছে কি না
        if all(col in df.columns for col in CHECK_COLUMNS):
            # ডুপ্লিকেট চেক (user ও pass এর ভিত্তিতে)
            duplicate_df = df[df.duplicated(subset=CHECK_COLUMNS, keep='first')]
            original_df = df.drop_duplicates(subset=CHECK_COLUMNS, keep='first')

            # Excel ফাইল তৈরি
            original_df.to_excel(clean_filename, index=False)
            duplicate_df.to_excel(removed_filename, index=False)

            # ফাইলগুলো ইউজারকে পাঠানো
            with open(clean_filename, 'rb') as f:
                await update.message.reply_document(
                    document=f, 
                    caption=f"✅ ইউনিক ডাটা (Total: {len(original_df)})"
                )
            
            with open(removed_filename, 'rb') as f:
                await update.message.reply_document(
                    document=f, 
                    caption=f"🗑️ ডুপ্লিকেট ডাটা (Total: {len(duplicate_df)})"
                )
        else:
            found_cols = ", ".join(df.columns.tolist())
            await update.message.reply_text(
                f"ভুল: আপনার ফাইলে 'user' এবং 'pass' কলাম পাওয়া যায়নি।\n\n"
                f"আপনার ফাইলের কলামগুলো হলো: {found_cols}"
            )

    except Exception as e:
        await update.message.reply_text(f"একটি সমস্যা হয়েছে: {str(e)}")
    
    finally:
        # টেম্পোরারি ফাইল মুছে ফেলা
        for f in [input_file, clean_filename, removed_filename]:
            if os.path.exists(f):
                os.remove(f)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("বট চলছে... আপনার ফাইলে 'user' এবং 'pass' কলাম থাকা নিশ্চিত করুন।")
    app.run_polling()

if __name__ == '__main__':
    main()
