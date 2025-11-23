import telebot
import schedule
import time
import random
import sqlite3
import logging
from datetime import datetime, timedelta
import os
# تنظیمات لاگ برای سرور
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# تنظیمات اصلی
TOKEN = "8251436392:AAHSnX3ULH1fbVG13Iu7QdiTw-_Wfn3vrMI"
CHAT_ID = 7904316019

bot = telebot.TeleBot(TOKEN)

# مسیر دیتابیس در سرور
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zahra_medicine.db')

# ایجاد دیتابیس برای ذخیره اطلاعات
def init_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS medicine_log
                 (id INTEGER PRIMARY KEY, 
                  timestamp TEXT, 
                  medicine_type TEXT, 
                  status TEXT,
                  response_time INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_scores
                 (user_id INTEGER PRIMARY KEY,
                  total_score INTEGER,
                  streak_days INTEGER,
                  last_activity TEXT)''')
    conn.commit()
    conn.close()

# init_database()

# سیستم امتیازدهی
# class ScoreSystem:
#     def __init__(self, user_id):
#         self.user_id = user_id
    
#     def add_score(self, points, reason=""):
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
        
#         # دریافت امتیاز فعلی
#         c.execute("SELECT total_score, streak_days FROM user_scores WHERE user_id = ?", (self.user_id,))
#         result = c.fetchone()
        
#         current_date = datetime.now().strftime("%Y-%m-%d")
        
#         if result:
#             total_score, streak_days = result
#             total_score += points
#             streak_days += 1
#             c.execute("UPDATE user_scores SET total_score = ?, streak_days = ?, last_activity = ? WHERE user_id = ?",
#                      (total_score, streak_days, current_date, self.user_id))
#         else:
#             total_score = points
#             streak_days = 1
#             c.execute("INSERT INTO user_scores (user_id, total_score, streak_days, last_activity) VALUES (?, ?, ?, ?)",
#                      (self.user_id, total_score, streak_days, current_date))
        
#         conn.commit()
#         conn.close()
#         return total_score, streak_days

# پیام‌های فوری و انگیزشی
MEDICINE_ALERTS = {
    "morning": [
        "🌅 **عملیات طلوع آفتاب!** 🌅\n⏰ ساعت ۶:۰۰\n💊 ماموریت: مصرف قرص صبحگاهی\n⚡ وضعیت: فوری!\n🏃‍♀️ بلند شو و اقدام کن!",
        "🚨 **آلارم صبحگاهی!** 🚨\n☀️ طلوع آفتاب = زمان دارو\n💊 قرص صبحتو بخور!\n🎯 مهلت: ۵ دقیقه!",
        "🔔 **بیدار شو قهرمان!** 🔔\n⏰ ۶:۰۰ - موقع داروی صبح\n💪 بدن تو منتظر سوخت‌رسانیه!\n⚡ سریع اقدام کن!"
    ],
    "noon": [
        "☀️ **ماموریت نیمروز!** ☀️\n⏰ ساعت ۱۲:۰۰\n💊 داروی ظهرتو مصرف کن!\n🔥 انرژی نیمروز رو از دست نده!",
        "⚡ **عملیات ظهر!** ⚡\n⏰ ۱۲:۰۰ - زمان دارو\n💊 مصرف فوری قرص ظهر\n🎯 هدف: سلامتی پایدار!",
        "🌞 **هشدار ظهرگاهی!** 🌞\n⏰ ساعت ۱۲:۰۰\n💊 موقع داروی ظهره!\n🏃‍♀️ فوراً اقدام کن!"
    ],
    "evening": [
        "🌇 **یگان عصرگاهی!** 🌇\n⏰ ساعت ۱۸:۰۰\n💊 قرص عصرتو بخور!\n⚡ وضعیت: بسیار مهم!",
        "🔴 **آلارم غروب!** 🔴\n⏰ ۶ عصر - زمان دارو\n💊 مصرف فوری قرص عصر\n🎯 ماموریت: بهبودی سریع!",
        "🌆 **عملیات عصر!** 🌆\n⏰ ساعت ۱۸:۰۰\n💊 داروی عصرتو فراموش نکن!\n⚡ اقدام فوری!"
    ],
    "midnight": [
        "🌙 **ماموریت نیمه‌شب!** 🌙\n⏰ ساعت ۰۰:۰۰\n💊 آخرین داروی روز رو بخور!\n🎯 پایان موفق روز!",
        "🔵 **آلارم نیمه‌شب!** 🔵\n⏰ ۱۲ شب - زمان دارو\n💊 قرص شبانه مصرف شود!\n⚡ اقدام قبل از خواب!",
        "🌌 **عملیات شبانه!** 🌌\n⏰ ساعت ۰۰:۰۰\n💊 داروی شب رو بخور!\n🌜 خواب راحت تضمینی!"
    ]
}

MOTIVATIONAL_MESSAGES = [
    "💪 **تو قوی‌تری از چیزی که فکر می‌کنی!**",
    "🌟 **هر دارو یک قدم به سمت سلامتی کامل!**",
    "🎯 **تعهد تو تحسین‌برانگیزه!**",
    "🔥 **آفرین! داری قوی‌تر می‌شی!**",
    "💖 **سلامتی تو باارزش‌ترین سرمایه‌ست!**"
]

# سیستم ارسال پیام
def send_medicine_alert(medicine_type):
    try:
        message = random.choice(MEDICINE_ALERTS[medicine_type])
        
        # افزودن پیام انگیزشی تصادفی
        if random.random() < 0.3:  # 30% شانس
            message += f"\n\n{random.choice(MOTIVATIONAL_MESSAGES)}"
        
        bot.send_message(CHAT_ID, message)
        
        # ثبت در دیتابیس
        log_medicine_alert(medicine_type, "sent")
        
        logging.info(f"✅ پیام {medicine_type} ارسال شد")
        
    except Exception as e:
        logging.error(f"❌ خطا در ارسال: {e}")

def log_medicine_alert(medicine_type, status, response_time=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO medicine_log (timestamp, medicine_type, status, response_time) VALUES (?, ?, ?, ?)",
             (datetime.now().isoformat(), medicine_type, status, response_time))
    conn.commit()
    conn.close()

# سیستم پاداش
# def send_daily_reward():
#     try:
#         score_system = ScoreSystem(CHAT_ID)
#         total_score, streak_days = score_system.add_score(25, "daily_reward")
        
#         reward_messages = [
#             f"🎉 **ماموریت روزانه تکمیل شد!** 🎉\n🏆 امتیاز تو: {total_score}\n🔥 streak: {streak_days} روز متوالی!",
#             f"⭐ **آفرین! امروز رو عالی پشت سر گذاشتی!** ⭐\n💎 امتیاز کل: {total_score}\n🚀 ادامه بده قهرمان!",
#             f"🌈 **عملکرد درخشان!** 🌈\n🎯 امتیاز: {total_score}\n💫 {streak_days} روز متوالی موفق!"
#         ]
        
#         bot.send_message(CHAT_ID, random.choice(reward_messages))
#         logging.info("✅ پاداش روزانه ارسال شد")
        
#     except Exception as e:
#         logging.error(f"❌ خطا در پاداش: {e}")

# گزارش هفتگی
# def send_weekly_report():
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
        
#         # آمار ۷ روز گذشته
#         week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
#         c.execute('''SELECT COUNT(*) FROM medicine_log 
#                     WHERE date(timestamp) >= ? AND status = 'taken' ''', (week_ago,))
#         medicines_taken = c.fetchone()[0]
        
#         c.execute("SELECT total_score, streak_days FROM user_scores WHERE user_id = ?", (CHAT_ID,))
#         result = c.fetchone()
#         total_score = result[0] if result else 0
#         streak_days = result[1] if result else 0
        
#         conn.close()
        
#         performance = "🏅 عالی" if medicines_taken >= 20 else "✅ خوب" if medicines_taken >= 15 else "⚠️ نیاز به بهبود"
        
#         report = f"""
# 📊 **گزارش هفتگی سلامتی** 📊
# 📅 دوره: ۷ روز گذشته
# 💊 داروهای مصرف شده: {medicines_taken} از ۲۸
# 📈 عملکرد: {performance}
# ⭐ امتیاز کل: {total_score}
# 🔥 روزهای متوالی: {streak_days}
# 🎯 هدف هفته آینده: بهبود مستمر!
#         """
        
#         bot.send_message(CHAT_ID, report)
#         logging.info("✅ گزارش هفتگی ارسال شد")
        
#     except Exception as e:
#         logging.error(f"❌ خطا در گزارش: {e}")

# زمان‌بندی اصلی
schedule.every().day.at("06:00").do(send_medicine_alert, "morning")
schedule.every().day.at("12:00").do(send_medicine_alert, "noon")
schedule.every().day.at("18:00").do(send_medicine_alert, "evening")
schedule.every().day.at("00:00").do(send_medicine_alert, "midnight")

# پاداش روزانه - ساعت ۱۱ شب
# schedule.every().day.at("23:00").do(send_daily_reward)

# # گزارش هفتگی - یکشنبه‌ها ساعت ۱۰ شب
# schedule.every().monday.at("22:00").do(send_weekly_report)

# شروع ربات
logging.info("🤖 ربات دارویی پیشرفته زهرا فعال شد!")
logging.info("⏰ زمان‌بندی‌ها:")
logging.info("   - ۰۶:۰۰ صبح")
logging.info("   - ۱۲:۰۰ ظهر")
logging.info("   - ۱۸:۰۰ عصر") 
logging.info("   - ۰۰:۰۰ شب")
logging.info("   - ۲۳:۰۰ پاداش روزانه")
logging.info("   - یکشنبه ۲۲:۰۰ گزارش هفتگی")

# تست اولیه
try:
    test_msg = "🚀 **ربات روی سرور ابری فعال شد!**\n💊 از اینجا به بعد همیشه در دسترسم!\n⏰ پیام‌ها مطابق برنامه ارسال می‌شوند"
    bot.send_message(CHAT_ID, test_msg)
    logging.info("✅ پیام راه‌اندازی ارسال شد")
except Exception as e:
    logging.error(f"❌ خطا در تست اولیه: {e}")

# حلقه اصلی زمان‌بندی
logging.info("🔄 وارد حلقه اصلی...")
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception as e:
        logging.error(f"❌ خطا در حلقه اصلی: {e}")
        time.sleep(10)