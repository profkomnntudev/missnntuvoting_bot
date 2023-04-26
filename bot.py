import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import os
import json
import psycopg2

conn = psycopg2.connect(dbname='root', user='root', 
                        password='akiyoss', host='localhost')

print(conn)
arr = os.listdir("./photos")

f = open('womans.json', encoding="UTF-8")
womans = json.load(f)
f.close()
womans = womans["womans"]

token='6174938640:AAFTvR0oaSESAgj92KuARrFEVowqoL8UR8I'
bot=telebot.TeleBot(token)

TEST = -1001814915286
PROD = -1001811677615

vote_ended = False
messageIds = []

@bot.message_handler(commands=['endvoting'])
def end_voting(message):
	if message.chat.id in [423894060, 1556653923]:
		global vote_ended
		vote_ended = True
		bot.send_message(message.chat.id, "Голосование окончено")


def gen_markup(cbdata):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    split = cbdata.split(".")
    markup.add(InlineKeyboardButton(f"Проголосовать ({split[2]})", callback_data=cbdata))
    return markup


def edit_messages(chatId):
	cursor = conn.cursor()
	i = 0
	msg = None
	for msgs in messageIds:
		if msgs['chatId'] == chatId:
			msg = msgs['messages']
	for woman in womans:
		cursor.execute(f'SELECT COUNT(*) FROM voting WHERE woman = \'{woman["tag"]}\'')
		res = cursor.fetchall()
		try:
			bot.edit_message_reply_markup(chat_id=chatId, message_id=msg[i].id, reply_markup=gen_markup(f'{woman["nameWHO"]}.{woman["tag"]}.{res[0][0]}'))

		except ApiTelegramException:
			pass
		i = i + 1

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
	if vote_ended: 
		bot.send_message(call.from_user.id, "Голосование окончено")
		return
	data = call.data.split(".")
	cursor = conn.cursor()
	cursor.execute(f"SELECT * FROM voting WHERE tg_id = \'{call.from_user.id}\'")
	votes = cursor.fetchall()
	if(votes == []):
		bot.send_message(call.from_user.id, f"Вы успешно проголосовали за {data[0]}")
		cursor.execute(f"INSERT INTO voting (tg_id, woman) VALUES (\'{call.from_user.id}\', \'{data[1]}\')")
		cursor.close()
		conn.commit()
		edit_messages(call.from_user.id)
	else: 
		bot.send_message(call.from_user.id, "Вы уже проголосовали")
                
@bot.message_handler(commands=['winners'])
def win_message(message):
	if message.chat.id in [423894060, 1556653923]:
		cursor = conn.cursor()
		reply_text = "Результаты: "
		for woman in womans:
			cursor.execute(f'SELECT COUNT(*) FROM voting WHERE woman = \'{woman["tag"]}\'')
			res = cursor.fetchall()
			reply_text = reply_text + f'\n{woman["name"]}: {res[0][0]}'
		bot.send_message(message.chat.id, reply_text)

@bot.message_handler(commands=['update'])
def upd_message(message):
	edit_messages(message.chat.id)

@bot.message_handler()
def start_message(message):
	res = bot.get_chat_member(PROD, message.chat.id)
	cursor = conn.cursor()
	if res.status != "left" and res.status != "kicked":
		messages = []
		bot.send_message(message.chat.id, "Голосуй за понравившуюся участницу, но помни: повторно голосовать нелья, делай выбор обдуманно.\nТолько от тебя зависит, кто получит Мисс зрительских симпатий!")
		for woman in womans:
			cursor.execute(f'SELECT COUNT(*) FROM voting WHERE woman = \'{woman["tag"]}\'')
			res = cursor.fetchall()
			photo = open(woman["photo"], 'rb')
			messages.append(bot.send_photo(message.chat.id, photo, reply_markup=gen_markup(f'{woman["nameWHO"]}.{woman["tag"]}.{res[0][0]}')))
		global messageIds
		messageIds.append({"chatId": message.chat.id, "messages": messages})
	else:
		bot.send_message(message.chat.id,"Для участия в голосовании требуется подписаться на канал профсоюзной организации студентов НГТУ\n\nhttps://t.me/profkomngtu")
                
                

bot.infinity_polling()