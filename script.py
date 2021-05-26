
import asyncio
from datetime import datetime
import requests


def telegram_bot_sendtext(bot_message):
    
    bot_token = '1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY'
    bot_chatID = '-1001253024203'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()

def main1():
    #code whatever logic you want for the running here
    test = telegram_bot_sendtext("Testing Telegram bot")
    print(test)
	

def fire_and_forget(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, *kwargs)

    return wrapped


@fire_and_forget
def foo():
    main1()
    print("foo() completed")


def main():
    print("Hello")

    f = open("last_executed.txt", "r")
   
    last_run_date = datetime.strptime(f.read(), "%d-%m-%y").date()
    if datetime.now().date() > last_run_date:
        foo()
        #print("I didn't wait for foo()")

        f = open("last_executed.txt", "w")
        f.write(datetime.now().strftime("%d-%m-%y"))
        f.close()
    
    return "This is sooo good"


if __name__ == '__main__':
    main()