import logging
import os
import time

from dotenv import load_dotenv
import requests
import telegram


class TelegramLogsHandler(logging.Handler):

    def __init__(self, bot, chat_id):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        try:
            self.bot.send_message(chat_id=self.chat_id, text=log_entry)
        except Exception:
            pass


def main():
    load_dotenv()
    DEVMAN_API_TOKEN = os.environ['DEVMAN_API_TOKEN']
    TG_API_KEY = os.environ['TG_API_KEY']
    TG_CHAT_ID = os.environ['TG_CHAT_ID']

    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'{DEVMAN_API_TOKEN}'
    }
    params = {}
    timestamp = None

    bot = telegram.Bot(token=TG_API_KEY)

    logger = logging.getLogger('devman_bot')
    logger.setLevel(logging.INFO)
    telegram_handller = TelegramLogsHandler(bot, TG_CHAT_ID)
    telegram_handller.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(telegram_handller)
    logger.info('Бот запущен.')

    while True:
        try:
            if timestamp:
                params['timestamp'] = timestamp

            raw_response = requests.get(url, headers=headers, params=params, timeout=95)
            raw_response.raise_for_status()
            response = raw_response.json()

            if response['status'] == 'timeout':
                timestamp = response['timestamp_to_request']
            else:
                timestamp = response['last_attempt_timestamp']

                lesson_title = response['new_attempts'][0]['lesson_title']
                lesson_url = response['new_attempts'][0]['lesson_url']
                message = (
                    'К сожалению, в работе нашлись ошибки.' 
                    if response['new_attempts'][0]['is_negative'] 
                    else 'Преподавателю всё понравилось, можно приступать к следующему уроку!'
                )
                result_message = f'У вас проверили работу: {lesson_title}\n{lesson_url}\n\n{message}'
                bot.send_message(chat_id=TG_CHAT_ID, text=result_message)

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            logger.warning('Ошибка подключения. Повторный запрос через 5 сек.')
            time.sleep(5)
        except requests.exceptions.HTTPError as e:
            logger.error(f'Сервер вернул ошибку: {e.response.status_code} {e.response.reason}\nПовторный запрос через 5 сек.')
            time.sleep(5)


if __name__ == '__main__':
    main()