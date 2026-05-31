import telebot
from telebot import types
import requests
import random
import time
import sys

# Твой токен Telegram-бота
TOKEN = '8932397702:AAFUOGZpBMh2HQ6BvmmNsPIUCzzQYiNHEfs'
bot = telebot.TeleBot(TOKEN)

# Настройки для генерации
RANDOM_LENGTH = 5  # Минимальная длина юзернейма в Telegram - 5 символов
CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"

def check_username(username):
    """Функция проверки занятости юзернейма через веб-версию Telegram"""
    try:
        # Расширенный User-Agent, чтобы Telegram не блокировал запросы как от бота
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        url = f"https://t.me/{username}"
        # Таймаут 10 секунд, чтобы скрипт не зависал при плохом соединении
        response = requests.get(url, headers=headers, timeout=10)
        
        # Если находим этот текст в HTML, значит страница "Not Found" и ник свободен
        if "if you have Telegram" in response.text:
            return True
    except Exception as e:
        print(f"Ошибка при проверке ника @{username}: {e}")
    return False

def get_main_keyboard():
    """Функция создания нижней клавиатуры"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_random = types.KeyboardButton("🎲 Проверить 1 случайный ник")
    btn_words = types.KeyboardButton("📖 Искать по словарю (words.txt)")
    markup.add(btn_random, btn_words)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def start_command(message):
    """Обработчик команды /start"""
    print(f"Пользователь {message.chat.id} запустил бота.")
    bot.send_message(
        message.chat.id, 
        "Привет! Я профессиональный бот для поиска свободных юзернеймов.\n\n"
        "Мои кнопки управления находятся в самом низу экрана (вместо клавиатуры для ввода текста). Выбери нужный режим:",
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Обработчик нажатия на кнопки"""
    
    # --- РЕЖИМ 1: СЛУЧАЙНЫЙ НИК ---
    if message.text == "🎲 Проверить 1 случайный ник":
        username = "".join(random.choice(CHARS) for _ in range(RANDOM_LENGTH))
        bot.send_message(message.chat.id, f"⏳ Генерирую и проверяю случайный ник: @{username}...")
        
        if check_username(username):
            bot.send_message(message.chat.id, f"✅ Свободен: @{username}")
        else:
            bot.send_message(message.chat.id, f"❌ Занят: @{username}")

    # --- РЕЖИМ 2: ПОИСК ПО СЛОВАРЮ ---
    elif message.text == "📖 Искать по словарю (words.txt)":
        bot.send_message(
            message.chat.id, 
            "🚀 Запускаю проверку по словарю `words.txt`...\n\n"
            "Я буду проверять слова с паузой в 3 секунды, чтобы Telegram не выдал бан. "
            "Если найду свободный ник — сразу пришлю его сюда. Просто оставь бота работать.", 
            parse_mode="Markdown"
        )
        
        try:
            # Открываем файл безопасно, с правильной кодировкой
            with open('words.txt', 'r', encoding='utf-8') as f:
                words = f.readlines()
            
            if not words:
                bot.send_message(message.chat.id, "⚠️ Ошибка: Файл `words.txt` абсолютно пуст. Добавь туда слова.")
                return

            found_count = 0
            # Перебираем все слова
            for line in words:
                word = line.strip().lower()
                
                # Telegram не дает регистрировать ники короче 5 символов
                if len(word) >= 5:
                    print(f"Проверяю слово из словаря: {word}")
                    if check_username(word):
                        bot.send_message(message.chat.id, f"🔥 НАЙДЕН СВОБОДНЫЙ НИК: @{word}")
                        found_count += 1
                    
                    # Жесткая пауза для защиты от блокировки IP-адреса на сервере
                    time.sleep(3.0)
            
            bot.send_message(message.chat.id, f"🏁 Проверка словаря полностью завершена!\nНайдено свободных ников: {found_count}")
            
        except FileNotFoundError:
            bot.send_message(
                message.chat.id, 
                "❌ КРИТИЧЕСКАЯ ОШИБКА: Файл `words.txt` не найден!\n\n"
                "Пожалуйста, зайди на GitHub и создай файл `words.txt` в той же папке, где находится файл `bot.py`."
            )
            
    # --- ОБРАБОТКА ЛЮБОГО ДРУГОГО ТЕКСТА ---
    else:
        bot.send_message(
            message.chat.id, 
            "Пожалуйста, используй только кнопки внизу экрана для управления ботом.", 
            reply_markup=get_main_keyboard()
        )

# ==========================================
# ЗАПУСК БОТА И ЗАЩИТА ОТ ОШИБОК 409
# ==========================================
if __name__ == '__main__':
    print("Начинаю процесс запуска...")
    
    # Сброс вебхуков убивает старые зависшие процессы в облаке
    try:
        bot.remove_webhook()
        time.sleep(1)
        print("Старые соединения (вебхуки) успешно очищены.")
    except Exception as e:
        print(f"Предупреждение при очистке вебхука: {e}")

    print("Бот успешно запущен и готов к работе в режиме polling!")
    
    # Бесконечный цикл работы с защитой от обрывов связи
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Произошла критическая ошибка при работе (Polling): {e}")
        # Если произошел сбой, ждем 5 секунд и завершаем процесс, чтобы Render мог его перезапустить
        time.sleep(5)
        sys.exit(1)
