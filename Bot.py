import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from datetime import datetime, timedelta
import random
import pg8000

# Bot tokeni
API_TOKEN = '8935181978:AAEPXusfIVG-z_ype7F1pZn_uKTUmwpJE8U'
bot = telebot.TeleBot(API_TOKEN)

# 🛑 DIQQAT: Pastdagi qo'shtirnoq ichiga hozirgina bazadan nusxalab olgan uzun havolangizni joylashtiring!
DATABASE_URL = "BU_YERGA_NUSXALANGAN_EXTERNAL_URL_NI_QO_YING"

def get_db_connection():
    # Havolani pg8000 tushunadigan qismlarga ajratib olish
    clean_url = DATABASE_URL.replace("postgresql://", "")
    credentials, rest = clean_url.split("@")
    db_user, db_pass = credentials.split(":")
    
    if "?" in rest:
        rest = rest.split("?")[0]
        
    host_port, db_name = rest.split("/")
    db_host, db_port = host_port.split(":")
    
    return pg8000.connect(
        user=db_user,
        password=db_pass,
        host=db_host,
        database=db_name,
        port=int(db_port),
        ssl_context=True
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_spins (
            user_id BIGINT PRIMARY KEY,
            last_spin_time TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS available_numbers (
            num INT PRIMARY KEY
        )
    ''')
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM available_numbers')
    count = cursor.fetchone()[0]
    if count == 0:
        for i in range(1, 15):
            cursor.execute('INSERT INTO available_numbers (num) VALUES (%s) ON CONFLICT DO NOTHING', (i,))
        conn.commit()
    
    cursor.close()
    conn.close()

COOLDOWN_HOURS = 24

@bot.message_handler(commands=['start'])
def send_welcome(message):
    web_app_url = "https://chorniy.onrender.com" 
    
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    web_app_info = WebAppInfo(url=web_app_url)
    btn = KeyboardButton(text="🎰 Barabanni aylantirish", web_app=web_app_info)
    markup.add(btn)
    
    bot.send_message(
        message.chat.id, 
        f"Salom {message.from_user.first_name}! Noyob raqamlar barabaniga xush kelibsiz.\n"
        f"Har bir odamga faqat bitta takrorlanmas raqam tushadi. Har {COOLDOWN_HOURS} soatda 1 marta o'ynash mumkin.", 
        reply_markup=markup
    )

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    user_id = message.from_user.id
    current_time = datetime.now()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT last_spin_time FROM user_spins WHERE user_id = %s', (user_id,))
    row = cursor.fetchone()
    if row:
        last_spin = row[0]
        next_spin_time = last_spin + timedelta(hours=COOLDOWN_HOURS)
        if current_time < next_spin_time:
            remaining_time = next_spin_time - current_time
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            bot.send_message(message.chat.id, f"❌ Bugun aylantirib bo'ldingiz! Keyingi urinishgacha: {hours} soat {minutes} daqiqa bor.")
            cursor.close()
            conn.close()
            return

    cursor.execute('SELECT num FROM available_numbers')
    numbers = [r[0] for r in cursor.fetchall()]
    
    if not numbers:
        for i in range(1, 15):
            cursor.execute('INSERT INTO available_numbers (num) VALUES (%s) ON CONFLICT DO NOTHING', (i,))
        conn.commit()
        cursor.execute('SELECT num FROM available_numbers')
        numbers = [r[0] for r in cursor.fetchall()]

    chiqqan_son = random.choice(numbers)
    cursor.execute('DELETE FROM available_numbers WHERE num = %s', (chiqqan_son,))
    
    cursor.execute('''
        INSERT INTO user_spins (user_id, last_spin_time) 
        VALUES (%s, %s) 
        ON CONFLICT (user_id) DO UPDATE SET last_spin_time = EXCLUDED.last_spin_time
    ''', (user_id, current_time))
    
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM available_numbers')
    if cursor.fetchone()[0] == 0:
        for i in range(1, 15):
            cursor.execute('INSERT INTO available_numbers (num) VALUES (%s)', (i,))
        conn.commit()
        bot.send_message(message.chat.id, "📢 Diqqat! Hamma 14 ta raqam tarqatib bo'lindi. O'yin avtomatik ravishda yangidan boshlandi!")

    cursor.close()
    conn.close()
    
    bot.send_message(message.chat.id, f"🎉 Tabriklaymiz! Sizga mutlaqo noyob bo'lgan **{chiqqan_son}** raqami tushdi!")

if __name__ == '__main__':
    init_db()
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.polling(none_stop=True)
