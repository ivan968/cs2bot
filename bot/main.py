import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Замініть на свій токен та ID каналу
TELEGRAM_TOKEN = '7690922097:AAEjmxo9BYyOdlYADSUw1JylKeKrVhM-rOE'
CHANNEL_ID = '@kugisaki_n'

# URL сайту HLTV для парсингу турнірів
HLTV_URL = 'https://www.hltv.org/matches'

# Ініціалізація бота
bot = Bot(token=TELEGRAM_TOKEN)

# Змінна для інтервалу відправлення
send_interval = 3 * 60 * 60  # За замовчуванням 3 години

def fetch_hltv_matches():
    """
    Функція для парсингу матчів із сайту HLTV.org
    """
    response = requests.get(HLTV_URL)
    soup = BeautifulSoup(response.content, 'html.parser')

    matches = []

    # Знаходимо блоки матчів
    match_blocks = soup.find_all('div', class_='upcomingMatch')
    for block in match_blocks:
        try:
            time = block.find('div', class_='matchTime').text.strip()
            teams = block.find_all('div', class_='matchTeamName')
            team1 = teams[0].text.strip() if teams else 'N/A'
            team2 = teams[1].text.strip() if len(teams) > 1 else 'N/A'

            # Парсинг логотипів команд
            logos = block.find_all('img', class_='matchTeamLogo')
            team1_logo = logos[0]['src'] if logos else ''
            team2_logo = logos[1]['src'] if len(logos) > 1 else ''

            matches.append({
                'time': time,
                'team1': team1,
                'team2': team2,
                'team1_logo': team1_logo,
                'team2_logo': team2_logo,
            })
        except Exception as e:
            print(f"Error parsing match: {e}")

    return matches

def format_match_info(match):
    """
    Форматування інформації про матч для публікації у Telegram
    """
    return (f"🕒 *{match['time']}*\n"
            f"🏆 *{match['team1']}* vs *{match['team2']}*\n"
            f"🖼️ [Логотип {match['team1']}](https:{match['team1_logo']}) vs [Логотип {match['team2']}](https:{match['team2_logo']})")

def send_matches_to_channel():
    """
    Функція для відправки інформації до Telegram-каналу
    """
    matches = fetch_hltv_matches()
    if not matches:
        bot.send_message(chat_id=CHANNEL_ID, text="Немає інформації про нові матчі.")
        return

    for match in matches:
        message = format_match_info(match)
        bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='Markdown')

def set_interval(update, context):
    """
    Команда для налаштування інтервалу відправлення повідомлень
    """
    global send_interval

    try:
        args = context.args
        if len(args) != 1:
            update.message.reply_text("Вкажіть інтервал у годинах. Наприклад, /setinterval 2")
            return

        hours = int(args[0])
        if hours <= 0:
            update.message.reply_text("Інтервал має бути більше 0 годин.")
            return

        send_interval = hours * 60 * 60
        update.message.reply_text(f"Інтервал успішно встановлено на {hours} годин.")
    except ValueError:
        update.message.reply_text("Будь ласка, введіть число.")

def main():
    """
    Основна функція для запуску бота
    """
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    dispatcher = application.dispatcher

    # Додати команду для встановлення інтервалу
    dispatcher.add_handler(CommandHandler('setinterval', set_interval))

    application.run_polling()

    while True:
        try:
            send_matches_to_channel()
            time.sleep(send_interval)  # Використовуємо змінну інтервалу
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
