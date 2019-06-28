import sqlite3
from sqlite3 import Error
import os
import time
import datetime
import re
import random
import schedule
import cryptography

from apscheduler.schedulers.background import BackgroundScheduler
from slackclient import SlackClient
from cryptography.fernet import Fernet

conn = sqlite3.connect('/home/ubuntu/otakuBot/data/anime.db')
serverCursor = conn.cursor()

keyFile = open('/home/ubuntu/otakuBot/data/otakubot_token.key', 'rb')
key = keyFile.read()
keyFile.close()

f = Fernet(key)

encryptedTokenFile = open('/home/ubuntu/otakuBot/data/otakubot_token.encrypted', 'rb')
encryptedToken = encryptedTokenFile.read()

decryptedToken = f.decrypt(encryptedToken)

SLACK_BOT_TOKEN = decryptedToken.decode()

# instantiate Slack client
slack_client = SlackClient(SLACK_BOT_TOKEN)
# starterbot's user ID in Slack: value is assigned after the bot starts up
otakuBotID = None

# constants
RTM_READ_DELAY = 0.5 # 0.5 second delay in reading events

def stdOut(s):
    curDate = datetime.datetime.today().strftime('%Y-%m-%d')
    curTime = datetime.datetime.now().strftime('%H:%M:%S')
    logFile = open((("/home/ubuntu/logs/{0}.log").format(curDate)),"a")
    logFile.write(("{0}:  {1}\n").format(curTime,s))
    logFile.close()
    return

def logIt():
    curDate = datetime.datetime.today().strftime('%Y-%m-%d')
    curTime = datetime.datetime.now().strftime('%H:%M:%S')
    logFile = open((("/home/ubuntu/logs/{0}.log").format(curDate)),"a")
    logFile.write(("{0}:  Otaku 15 minute check in!\n").format(curTime))
    logFile.close()
    return

schedule.every(15).minutes.do(logIt)

def SQLReturn(aConn,sqlCmd):
	reportCur = aConn.cursor()
	reportCur.execute(sqlCmd)
	SQLResults = reportCur.fetchall()
	reportCur.close()
	return SQLResults
	
def insertQuote (aUser,theQuote):
	newCur = conn.cursor()
	newCur.execute(("""
		INSERT INTO 
			Quotes (User, Words) 
		VALUES
			('{0}','{1}');
	""").format(aUser,theQuote))
	newCur.close()
	conn.commit()
	return

def insertAniMusic (aUser,theLink):
	newCur = conn.cursor()
	newCur.execute(("""
		INSERT INTO 
			Music (Category, User, Link) 
		VALUES
			('Anime','{0}','{1}');
	""").format(aUser,theLink))
	newCur.close()
	conn.commit()
	return

def insertEngMusic (aUser,theLink):
	newCur = conn.cursor()
	newCur.execute(("""
		INSERT INTO 
			Music (Category, User, Link) 
		VALUES
			('English','{0}','{1}');
	""").format(aUser,theLink))
	newCur.close()
	conn.commit()
	return

def insertIcon (aUser,theLink):
	newCur = conn.cursor()
	newCur.execute(("""
		INSERT INTO 
			Music (Category, User, Link) 
		VALUES
			('Iconic','{0}','{1}');
	""").format(aUser,theLink))
	newCur.close()
	conn.commit()
	return

def deleteQuote (quoteID):
	newCur = conn.cursor()
	newCur.execute(("""
		DELETE
		FROM
			Quotes
		WHERE
			ID == {0};
	""").format(quoteID))
	newCur.close()
	conn.commit()
	return

def getQuote(aConn):
	sqlCmd = "SELECT Words FROM Quotes;"
	results = SQLReturn(aConn,sqlCmd)
	allQuotes = []
	for quote in results:
		allQuotes.append(quote)
	return (random.choice(allQuotes))

def getAniMusic(aConn):
	sqlCmd = "SELECT Link FROM Music WHERE Category = 'Anime';"
	results = SQLReturn(aConn,sqlCmd)
	allQuotes = []
	for quote in results:
		allQuotes.append(quote)
	return (random.choice(allQuotes))

def getEngMusic(aConn):
	sqlCmd = "SELECT Link FROM Music WHERE Category = 'English';"
	results = SQLReturn(aConn,sqlCmd)
	allQuotes = []
	for quote in results:
		allQuotes.append(quote)
	return (random.choice(allQuotes))

def getIconic(aConn):
	sqlCmd = "SELECT Link FROM Music WHERE Category = 'Iconic';"
	results = SQLReturn(aConn,sqlCmd)
	allQuotes = []
	for quote in results:
		allQuotes.append(quote)
	return (random.choice(allQuotes))

def getAllQuotes(aConn):
	sqlCmd = "SELECT ID, Words FROM Quotes;"
	results = SQLReturn(aConn,sqlCmd)
	allQuotes = []
	for quote in results:
		allQuotes.append(quote)
	newStr = "All the Quotes\n"
	for item in allQuotes:
		i = 1
		for place in item:
			if i == 1:
				newStr += "ID: " + str(place) + "\n"
			if i == 2:
				newStr += "Words: " + str(place) + "\n\n"
			i += 1
	return newStr
	
def EODReportRange (date1, date2): # Gets a range summary of the VM number and status reported
	cmd = (("""
		SELECT 
			ServerNumber as [Server]
			, ServerStatus as [Status]
			, count(ServerStatus) as [Amount]
		FROM 
			Status
		WHERE 
			date(TimeStamp) BETWEEN '{0}' AND '{1}'
			AND ServerNumber IN('1','2','3','4','17')
		GROUP BY 
			ServerNumber
			,ServerStatus
	""").format(date1, date2))
	results = SQLReturn(conn,cmd)
	newStr = "Report for: " + date1 + " to " + date2 + "\n"
	for row in results:
		i = 1
		for item in row:
			if i == 1:
				newStr += "VM" + str(item) + " - "
			if i == 2:
				newStr += "Status: " + str(item) + " - "
			if i == 3:
				if item != 1:
					newStr += "Reported: " + str(item) + " times"
				else:
					newStr += "Reported: " + str(item) + " time"
			i += 1
		newStr += "\n"
	return newStr

def parseSlackInput(aText):
	if aText and len(aText) > 0:
		item = aText[0]
		if 'text' in item:
			msg = item['text'].strip(' ')
			chn = item['channel']
			usr = item['user']
			stp = item['ts']
			return [str(msg),str(chn),str(usr),str(stp)]
		else:
			return [None,None,None,None]

def inChannelResponse(channel,response):
	slack_client.api_call(
		"chat.postMessage",
		channel=channel,
		text=response,
		as_user=True
		)
	return

def threadedResponse(channel,response,stamp):
	slack_client.api_call(
		"chat.postMessage",
		channel=channel,
		text=response,
		thread_ts=stamp,
		as_user=True
		)
	return

def directResponse(someUser,text):
	slack_client.api_call(
		"chat.postMessage",
		channel=someUser,
		text=text,
		as_user=True
		)
	return

def parseQuote(someMsg):
	starter,theQuote = someMsg.split(' ', 1)
	return theQuote

def handle_command(command, channel, aUser, tStamp):
	"""
		Executes bot command if the command is known
	"""
	#command = command.lower()
	response = None
		# This is where you start to implement more commands!
	if command.lower().startswith("!help"):
		response = """I'm Otaku Bot!

			I don't do a lot yet. But watch out! I'm just getting started!
			
			!addquote[SPACE][A quote of your choice!] - I will remember your quote!
			!quote - I will reply with a random quote!

			!addAniMusic[SPACE][Link to a Japanese anime song] - I will remember your music!
			!addEngMusic[SPACE][Link to an English anime song] - I will remember your music!
			!addIconic[SPACE][Link to an iconic anime moment] - I will remember your moment!

			!animusic - I will reply with a Japanese anime song from memory!
			!engmusic - I will reply with an English anime song from memory!
			!iconic - I will show you an iconic anime moment!
			"""
		inChannelResponse(channel,response)
		return
	if command.lower().startswith("!addquote"):
		newQuote = str(command[10:])
		insertQuote(aUser,newQuote)
		threadedResponse(channel,"I'll try to remember: " + newQuote ,tStamp)
		stdOut("Quote Added: " + newQuote)
		return
	if command.lower().startswith("!quote"):
		aQuote = getQuote(conn)
		inChannelResponse(channel,aQuote)
		return
	if command.lower().startswith("!animusic"):
		aQuote = getAniMusic(conn)
		inChannelResponse(channel,aQuote)
		return
	if command.lower().startswith("!engmusic"):
		aQuote = getEngMusic(conn)
		inChannelResponse(channel,aQuote)
		return
	if command.lower().startswith("!iconic"):
		aQuote = getIconic(conn)
		inChannelResponse(channel,aQuote)
		return
	if command.lower().startswith("!onepunch"):
		inChannelResponse(channel,"https://www.youtube.com/watch?v=_TUTJ0klnKk")
		return
	if command.lower().startswith("!addanimusic"):
		newQuote = str(command[13:])
		insertAniMusic(aUser,newQuote)
		threadedResponse(channel,"I'll add this to the Anime music section: " + newQuote ,tStamp)
		stdOut("Anime Music Added: " + newQuote)
		return
	if command.lower().startswith("!addengmusic"):
		newQuote = str(command[13:])
		insertEngMusic(aUser,newQuote)
		threadedResponse(channel,"I'll add this to the English music section: " + newQuote ,tStamp)
		stdOut("English Music Added: " + newQuote)
		return
	if command.lower().startswith("!addiconic"):
		newQuote = str(command[11:])
		insertIcon(aUser,newQuote)
		threadedResponse(channel,"I'll add this to the Iconic moments section: " + newQuote ,tStamp)
		stdOut("Iconic Moment Added: " + newQuote)
		return
	if command.lower().startswith("!delquote"):
		if aUser == "UC176R92M":
			num = command[10:]
			deleteQuote(num)
			inChannelResponse(channel,"You have removed a quote.")
		else:
			inChannelResponse(channel,"You don't have permission to do that!")
		return
	if command.lower().startswith("!getquotes"):
		if aUser == "UC176R92M":
			inChannelResponse(channel,getAllQuotes(conn))
		else:
			inChannelResponse(channel,"You don't have permission to do that!")
		return
	if command.startswith("!test"):
		return
		response = (("""Text:{0}
				Channel:{1}
				TS:{2}
				User:{3}
				""").format(command,channel,tStamp,aUser))
		inChannelResponse(channel,response)
		return
	return
	# Sends the response back to the channel
	
if __name__ == "__main__":
	if slack_client.rtm_connect(with_team_state=False):
		stdOut("Otaku Bot connected and running!")
		# Read bot's user ID by calling Web API method `auth.test`
		otakuBotID = slack_client.api_call("auth.test")["user_id"]
	while True:
		try:
			command, channel,usr,stp = parseSlackInput(slack_client.rtm_read())
			if command:
				handle_command(command, channel,usr,stp)
		except:
			pass
                schedule.run_pending()
		time.sleep(RTM_READ_DELAY)
	else:
		stdOut("Connection failed. Exception traceback printed above.")
