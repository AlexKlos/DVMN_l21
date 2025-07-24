import os
import time

from dotenv import load_dotenv
import requests
import telegram


def main():
    load_dotenv()

    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        f'Authorization': os.getenv('DEVMAN_API_TOKEN')
    }
    params = {}
    timestamp = None

    bot = telegram.Bot(token=os.getenv('TG_API_KEY'))

    while True:
        try:
            if timestamp:
                params['timestamp'] = timestamp

            response = requests.get(url, headers=headers, params=params, timeout=95)
            json_response = response.json()
            print(json_response)

            if json_response['status'] == 'timeout':
                timestamp = json_response['timestamp_to_request']
            else:
                timestamp = json_response['last_attempt_timestamp']

                lesson_title = json_response['new_attempts'][0]['lesson_title']
                lesson_url = json_response['new_attempts'][0]['lesson_url']
                result_message = (
                    'К сожалению, в работе нашлись ошибки.' 
                    if json_response['new_attempts'][0]['is_negative'] 
                    else 'Преподавателю всё понравилось, можно приступать к следующему уроку!'
                )
                message = f'У вас проверили работу: {lesson_title}\n{lesson_url}\n\n{result}'
                bot.send_message(chat_id=os.getenv('TG_CHAT_ID'), text=result_message)

        except requests.exceptions.ReadTimeout:
            time.sleep(0.01)
        except requests.exceptions.ConnectionError:
            print('Ошибка подключения. Повторный запрос через 5 сек.')
            time.sleep(5)


if __name__ == '__main__':
    main()