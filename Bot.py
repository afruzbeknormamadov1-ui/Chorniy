import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from datetime import datetime, timedelta

# Siz bergan faol Telegram bot tokeni
API_TOKEN = '8935181978:AAEPXusfIVG-z_ype7F1pZn_uKTUmwpJE8U'
bot = telebot.TeleBot(API_TOKEN)

# Foydalanuvchilar vaqtini eslab qolish uchun lug'at
user_cooldowns = {}

# Cheklov vaqti: 720 soat
COOLDOWN_HOURS = 720

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Render'dagi baraban sahifangiz havolasi tayyorlab qo'yildi
    web_app_url = "https://chorniy.onrender.com" 
    
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    web_app_info = WebAppInfo(url=web_app_url)
    btn = KeyboardButton(text="🎰 Barabanni aylantirish", web_app=web_app_info)
    markup.add(btn)
    
    bot.send_message(
        message.chat.id, 
        f"Salom {message.from_user.first_name}! 1 dan 14 gacha sonlar bor omad barabaniga xush kelibsiz.\n"
        f"Barabanni har {COOLDOWN_HOURS} soatda faqat 1 marta aylantira olasiz.", 
        reply_markup=markup
    )

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    user_id = message.from_user.id
    current_time = datetime.now()
    
    # Vaqt cheklovini tekshirish
    if user_id in user_cooldowns:
        last_spin = user_cooldowns[user_id]
        next_spin_time = last_spin + timedelta(hours=COOLDOWN_HOURS)
        
        if current_time < next_spin_time:
            remaining_time = next_spin_time - current_time
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            bot.send_message(
                message.chat.id, 
                f"❌ Bugun barabanni aylantirib bo'ldingiz!\n"
                f"Keyingi urinishgacha: {hours} soat-u {minutes} daqiqa kutishingiz kerak."
            )
            return

    # Agar vaqt to'g'ri bo'lsa, barabandan qaytgan sonni qabul qilamiz
    chiqqan_son = message.web_app_data.data
    user_cooldowns[user_id] = current_time # Oxirgi aylantirgan vaqtini saqlaymiz
    
    bot.send_message(
        message.chat.id, 
        f"🎉 Tabriklaymiz! Sizga **{chiqqan_son}** raqami chiqdi!\n\n"
        f"Keyingi aylantirish imkoniyati {COOLDOWN_HOURS} soatdan keyin ochiladi."
    )

if __name__ == '__main__':
    print("Bot ishga tushdi...")
    bot.polling(none_stop=True)
