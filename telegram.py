import requests
import threading

from credentials import *

def telegram_bot_sendtext(bot_message):
	thread = threading.Thread(target=_telegram_bot_sendtext, args = [bot_message])
	thread.daemon = True
	thread.start()

def _telegram_bot_sendtext(bot_message):
	try:
	   send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

	   response = requests.get(send_text)

	   return response.json()
	except:
		pass
	 

if __name__ == "__main__":
	test = telegram_bot_sendtext("Datalogger launched")
#print(test)