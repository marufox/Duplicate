import os
import pandas as pd
import re
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= 🔧 [ কনফিগারেশন ] =================
BOT_TOKEN = "8260254278:AAE0ZTPrPVQExDHS0VWhA7T8f_Bp8S1gYiI"

def auto_adjust_column_width(file_path):
    """Excel ফাইলের কলামের প্রস্থ অটো সাইজ করে"""
    try:
        wb = load_workbook(file_path)
        ws = wb.active
        
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max(max_length + 2, 15), 60)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        wb.save(file_path)
    except:
        pass

def extract_from_columns(df):
    """শুধু A, B, C কলাম থেকে ডাটা নেয়া (D, E, F ইগনোর)"""
    all_data = []
    
    # শুধু প্রথম 3 কলাম নেওয়া (A, B, C)
    max_cols = min(3, df.shape[1])
    
    for idx, row in df.iterrows():
        username = ""
        password = ""
        twofa = ""
        
        # A কলাম (index 0) = username
        if max_cols >= 1 and pd.notna(row[0]):
            username = str(row[0]).strip()
        
        # B কলাম (index 1) = password
        if max_cols >= 2 and pd.notna(row[1]):
            password = str(row[1]).strip()
        
        # C কলাম (index 2) = 2fa
        if max_cols >= 3 and pd.notna(row[2]):
            twofa = str(row[2]).strip()
        
        # যদি username এবং password থাকে
        if username and password:
            # 2fa তে যদি বেশি টেক্সট থাকে, সেটা রাখা
            all_data.append([username, password, twofa])
    
    if all_data:
        df_clean = pd.DataFrame(all_data, columns=["username", "password", "2fa"])
        
        # খালি ডাটা বাদ
        df_clean = df_clean[(df_clean["username"].astype(str).str.strip() != "") & 
                            (df_clean["password"].astype(str).str.strip() != "")]
        
        # পাসওয়ার্ড অনুযায়ী সাজানো (একই পাসওয়ার্ড একসাথে)
        df_clean = df_clean.sort_values(by=["password", "username"])
        
        return df_clean
    
    return None

def extract_from_messy_data(df):
    """এলোমেলো ডাটা থেকে শুধু A, B, C খুঁজে বের করা"""
    all_data = []
    
    # পুরো ফাইল স্ক্যান করে শুধু A, B, C স্টাইলের ডাটা খোঁজা
    for idx, row in df.iterrows():
        for col_idx, val in enumerate(row):
            if pd.notna(val):
                text = str(val).strip()
                if text:
                    # চেষ্টা 1: স্পেস দিয়ে আলাদা কিনা
                    parts = text.split()
                    
                    if len(parts) >= 3:
                        # মনে হচ্ছে এটা A B C স্টাইলের ডাটা (username password 2fa)
                        username = parts[0]
                        password = parts[1]
                        twofa = ' '.join(parts[2:])
                        all_data.append([username, password, twofa])
                    elif len(parts) == 2:
                        # username আর password থাকতে পারে
                        username = parts[0]
                        password = parts[1]
                        twofa = ""
                        all_data.append([username, password, twofa])
    
    if all_data:
        df_clean = pd.DataFrame(all_data, columns=["username", "password", "2fa"])
        
        # খালি ডাটা বাদ
        df_clean = df_clean[(df_clean["username"].astype(str).str.strip() != "") & 
                            (df_clean["password"].astype(str).str.strip() != "")]
        
        # পাসওয়ার্ড অনুযায়ী সাজানো
        df_clean = df_clean.sort_values(by=["password", "username"])
        
        return df_clean
    
    return None

# ================= 🚀 [ স্টার্ট কমান্ড ] =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ *Duplicate Remover Bot Active!*\n\n"
        "📂 Send me a `.csv` or `.xlsx` file.\n\n"
        "🔧 *What this bot does:*\n"
        "• Reads ONLY columns A, B, C\n"
        "• Ignores columns D, E, F (extra data)\n"
        "• Works with clean OR messy data\n"
        "• Removes duplicate entries\n"
        "• Groups same passwords together\n\n"
        "📤 Output: `username | password | 2fa` (sorted by password)\n\n"
        "💡 Powered by MAX FUTURE",
        parse_mode="Markdown"
    )

# ================= 📂 [ ফাইল প্রসেসিং ] =================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = update.message.document.file_name
    input_file = f"input_{file_name}"
    unique_file = "Unique_Data.xlsx"
    duplicate_file = "Duplicate_Data.xlsx"

    try:
        # ফাইল ডাউনলোড
        file = await context.bot.get_file(update.message.document.file_id)
        await file.download_to_drive(input_file)

        await update.message.reply_text("⏳ Processing file...")

        # ফাইল লোড
        if file_name.lower().endswith('.csv'):
            try:
                df = pd.read_csv(input_file, encoding='utf-8', header=None)
            except:
                df = pd.read_csv(input_file, encoding='latin1', header=None)
        else:
            df = pd.read_excel(input_file, header=None)

        # প্রথমে চেষ্টা করা শুধু A, B, C কলাম হিসাবে নেওয়া
        clean_df = extract_from_columns(df)
        
        # যদি না পাওয়া যায়, তাহলে এলোমেলো ডাটা থেকে খোঁজা
        if clean_df is None or clean_df.empty:
            clean_df = extract_from_messy_data(df)
        
        if clean_df is None or clean_df.empty:
            await update.message.reply_text("❌ Could not extract data! Make sure columns A=username, B=password, C=2fa")
            return

        # ডুপ্লিকেট চেক (username + password + 2fa)
        duplicate_mask = clean_df.duplicated(subset=["username", "password", "2fa"], keep='first')
        unique_df = clean_df[~duplicate_mask]
        duplicate_df = clean_df[duplicate_mask]

        # ফাইল তৈরি
        unique_df.to_excel(unique_file, index=False)
        
        if not duplicate_df.empty:
            duplicate_df.to_excel(duplicate_file, index=False)
            auto_adjust_column_width(unique_file)
            auto_adjust_column_width(duplicate_file)
        else:
            auto_adjust_column_width(unique_file)

        # রিপোর্ট
        report = f"✅ *Results:*\n"
        report += f"📊 Original: {len(clean_df)} records\n"
        report += f"✅ Unique: {len(unique_df)} records\n"
        report += f"🗑️ Duplicates removed: {len(duplicate_df)} records\n\n"
        report += f"📌 Same passwords grouped together\n"
        report += f"📌 Columns D, E, F ignored"

        # ফাইল পাঠানো
        with open(unique_file, 'rb') as f:
            await update.message.reply_document(
                document=f,
                caption=report,
                parse_mode="Markdown"
            )

        if not duplicate_df.empty:
            with open(duplicate_file, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    caption=f"🗑️ *Duplicate Records* (Total: {len(duplicate_df)})",
                    parse_mode="Markdown"
                )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\n\n⚠️ Make sure file has A=username, B=password, C=2fa")

    finally:
        for f in [input_file, unique_file, duplicate_file]:
            if os.path.exists(f):
                os.remove(f)

# ================= 🔄 [ মেইন ] =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("=" * 50)
    print("✅ DUPLICATE REMOVER BOT STARTED")
    print("📌 Reads ONLY columns A, B, C")
    print("📌 Ignores columns D, E, F")
    print("📌 Groups same passwords together")
    print("💡 Send any Excel/CSV file")
    print("=" * 50)
    
    app.run_polling()

if __name__ == '__main__':
    main()
