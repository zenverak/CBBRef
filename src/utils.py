import logging.handlers
import json
import random
import re
import math
from datetime import datetime
from datetime import timedelta

import globals
import database
import wiki
import reddit

log = logging.getLogger("bot")


def getLinkToThread(threadID):
	return globals.SUBREDDIT_LINK + threadID


def startGame(homeCoach, awayCoach, startTime=None, location=None, station=None, homeRecord=None, awayRecord=None):
	log.debug("Creating new game between /u/{} and /u/{}".format(homeCoach, awayCoach))

	coachNum, result = verifyCoaches([homeCoach, awayCoach])
	if coachNum != -1:
		log.debug("Coaches not verified, {} : {}".format(coachNum, result))
		return "Something went wrong, someone is no longer an \
						acceptable coach. Please try to start the game again"

	homeTeam = wiki.getTeamByCoach(homeCoach.lower())
	awayTeam = wiki.getTeamByCoach(awayCoach.lower())
	for team in [homeTeam, awayTeam]:
		team['2PtAttempted'] = 0
		team['2PtMade'] = 0
		team['3PtAttempted'] = 0
		team['3PtMade'] = 0
		team['turnovers'] = 0
		team['FTAttempted'] = 0
		team['FTMade'] = 0
		team['posTime'] = 0
		team['record'] = None
		team['playclockPenalties'] = 0
		team['timeouts'] = globals.timeouts
		team['bonus'] = 'N'
		team['offRebound'] = 0
		team['defRebound'] = 0
		team['fouls'] = 0
		team['steals'] = 0
		team['blocks'] = 0

	game = newGameObject(homeTeam, awayTeam)
	if startTime is not None:
		game['startTime'] = startTime
	if location is not None:
		game['location'] = location
	if station is not None:
		game['station'] = station
	if homeRecord is not None:
		homeTeam['record'] = homeRecord
	if awayRecord is not None:
		awayTeam['record'] = awayRecord

	gameThread = getGameThreadText(game)
	gameTitle = "[GAME THREAD] {}{} @ {}{}".format(
		game['away']['name'],
		" {}".format(awayRecord) if awayRecord is not None else "",
		game['home']['name'],
		" {}".format(homeRecord) if homeRecord is not None else "")

	threadID = str(reddit.submitSelfPost(globals.SUBREDDIT, gameTitle, gameThread))
	game['thread'] = threadID
	log.debug("Game thread created: {}".format(threadID))

	gameID = database.createNewGame(threadID)
	game['dataID'] = gameID
	log.debug("Game database record created: {}".format(gameID))

	for user in game['home']['coaches']:
		database.addCoach(gameID, user, True)
		log.debug("Coach added to home: {}".format(user))
	for user in game['away']['coaches']:
		database.addCoach(gameID, user, False)
		log.debug("Coach added to away: {}".format(user))

	log.debug("Game started, posting tip ball comment")
	message = "The ball is throw in the air! {},  {}, Respond to my message \
				for a TIP number".format(getCoachString(game, 'home'),
											getCoachString(game, 'away')
											)
	sendGameComment(game, message, {'action': 'tip'})
	log.debug("Comment posted, now waiting on both")
	updateGameThread(game)
	coaches = [game['home']['coaches'][0], game['away']['coaches'][0]]
	sendTipNumberMessages(game, coaches)
	log.debug("Returning game started message")
	return "Game started. Find it [here]({}).".format(getLinkToThread(threadID))


def embedTableInMessage(message, table):
	if table is None:
		return message
	else:
		return "{}{}{})".format(message,
							globals.datatag,
							json.dumps(table, indent=4, sort_keys=True, default=str))


def extractTableFromMessage(message):
	datatagLocation = message.find(globals.datatag)
	if datatagLocation == -1:
		return None
	data = message[datatagLocation + len(globals.datatag):-1]
	try:
		table = json.loads(data)
		return table
	except Exception:
		return None


def verifyCoaches(coaches):
	coachSet = set()
	teamSet = set()
	for i, coach in enumerate(coaches):
		if coach in coachSet:
			return i, 'duplicate'
		coachSet.add(coach)

		team = wiki.getTeamByCoach(coach)
		if team is None:
			return i, 'team'
		if team['name'] in teamSet:
			return i, 'same'
		teamSet.add(team['name'])

		game = database.getGameByCoach(coach)
		if game is not None:
			return i, 'game'

	return -1, None


def flair(team):
#	print (team)
	return "[{}](#f/{})".format(team['name'], team['tag'])


def renderTime(time):
	return "{}:{}".format(str(math.trunc(time / 60)), str(time % 60).zfill(2))

def get_percent(game, team, stat):
	'''
	Used to set percentage. This prevents division by zero cases for beginning
	of game when a lot of stats will be zero
	'''
	if stat == '3':
		if game[team]['3PtAttempted'] == 0:
			return 0
		return game[team]['3PtMade']/(1.0 *game[team]['3PtAttempted'])
	elif stat == 'free':
		if game[team]['FTAttempted'] == 0:
			return 0
		return game[team]['FTMade']/(1.0 *game[team]['FTAttempted'])
	else:
		if game[team]['3PtAttempted'] == 0 and game[team]['2PtAttempted']==0:
			return 0
		return (game[team]['3PtMade']+game[team]['2PtMade'])/(1.0 *(game[team]['3PtAttempted']+game[team]['2PtAttempted']))



def renderGame(game):
	bldr = []
	bldr.append(flair(game['away']))
	bldr.append(" **")
	bldr.append(game['away']['name'])
	bldr.append("** @ ")
	bldr.append(flair(game['home']))
	bldr.append(" **")
	bldr.append(game['home']['name'])
	bldr.append("**\n\n")

	if game['startTime'] is not None:
		bldr.append(" **Game Start Time:** ")
		bldr.append(game['startTime'])
		bldr.append("\n\n")

	if game['location'] is not None:
		bldr.append(" **Location:** ")
		bldr.append(game['location'])
		bldr.append("\n\n")

	if game['station'] is not None:
		bldr.append(" **Watch:** ")
		bldr.append(game['station'])
		bldr.append("\n\n")


	bldr.append("\n\n")

	for team in ['away', 'home']:
		made = game[team]['2PtMade']+game[team]['3PtMade']
		att = game[team]['2PtAttempted']+game[team]['3PtAttempted']
		bldr.append(flair(game[team]))
		bldr.append("\n\n")
		bldr.append("Shooting|Shooting %|3pters|3pt %|Free Throws|Free Throw %\
											|Turnovers|Fouls|Bonus|Timeouts\n")
		bldr.append(":-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:\n")
		bldr.append("{}/{}|{} %|{}/{}|{} %|{}/{}|{} %|{}|{}|{}|{}".format(
			made,
			att,
			get_percent(game, team, 'total'),
			game[team]['3PtMade'],
			game[team]['3PtAttempted'],
			get_percent(game, team, '3'),
			game[team]['FTMade'],
			game[team]['FTAttempted'],
			get_percent(game, team, 'free'),
			game[team]['turnovers'],
			game[team]['fouls'],
			game[team]['bonus'],
			game[team]['timeouts']))
		bldr.append("\n\n___\n")

	bldr.append("Playclock|Half\n")
	bldr.append(":-:|:-:\n")
	bldr.append("{}|{}\n".format(
		renderTime(game['status']['clock']),
		game['status']['half']
		))
	bldr.append("\n___\n\n")
	if game['isOverTime']:
		bldr.append("Team|H1|H2|")
		for i in range(1,game['half']+1-2):
			bldr.append("OT{}|".format(i))
		bldr.append('Total\n')
		bldr.append(":-:|:-:|:-:|")
		for i in range(1,game['half']+1-2):
			bldr.append(":-:|".format(i))
		bldr.append(':-:\n')
	else:
		bldr.append("Team|H1|H2|Total\n")
		bldr.append(":-:|:-:|:-:|:-:\n")
	for team in ['away', 'home']:
		bldr.append(flair(game[team]))
		bldr.append('|')
		bldr.append(str(game['score']['halves'][0][team]))
		bldr.append('|')
		bldr.append(str(game['score']['halves'][1][team]))
		bldr.append('|')
		if game['isOverTime']:
			for i in range(3, int(game['half'])+1):
				bldr.append(str(game['score']['halves'][i][team]))
				bldr.append('|')
			bldr.append(str(game['score'][team]))
		else:
			bldr.append(str(game['score'][team]))
		bldr.append('\n')
	return ''.join(bldr)


def coinToss():
	return random.choice([True, False])


def playNumber():
	return random.randint(0, globals.maxRange)


def rngNumber():
	##randint is inclusive on both ends
	return random.randint(1, globals.maxRange)


def getGameByThread(thread):
	threadText = reddit.getSubmission(thread).selftext
	return extractTableFromMessage(threadText)


def getTipWinner(awayTip,homeTip,botTip):
	a = awayTip
	h = homeTip
	b = botTip
	log.debug('homeTip is {}\nawayTip is {}\nbotTipis {}'.format(h,a,b))
	hDiff = abs(b - h)
	aDiff = abs(b - a)
	if hDiff <= aDiff:
		return 'home'
	else:
		return 'away'


def getGameByUser(user):
	dataGame = database.getGameByCoach(user)
	if dataGame is None:
		return None
	game = getGameByThread(dataGame['thread'])
	game['dataID'] = dataGame['id']
	game['thread'] = dataGame['thread']
	game['errored'] = dataGame['errored']
	return game


def getGameThreadText(game):
	threadText = renderGame(game)
	return embedTableInMessage(threadText, game)


def updateGameThread(game):
	updateGameTimes(game)
	if 'thread' not in game:
		log.error("No thread ID in game when trying to update")
	game['dirty'] = False
	threadText = getGameThreadText(game)
	reddit.editThread(game['thread'], threadText)


def isCoachHome(game, coach):
	if coach.lower() in game['home']['coaches']:
		return True
	elif coach.lower() in game['away']['coaches']:
		return False
	else:
		return None


def sendGameMessage(isHome, game, message, dataTable):
	reddit.sendMessage(game[('home' if isHome else 'away')]['coaches'],
			   "{} vs {}".format(game['home']['name'], game['away']['name']),
			   embedTableInMessage(message, dataTable))
	return reddit.getRecentSentMessage().id


def sendGameComment(game, message, dataTable=None):

	commentResult = reddit.replySubmission(game['thread'], embedTableInMessage(message, dataTable))
	tipped = False
	try:
		tipped =  game['status']['tipped']
	except:
		tipped = False
	if not tipped:
		log.debug("sent result of tip to game thread")
	else:
		game['waitingId'] = commentResult.fullname
		log.debug("Game comment sent, now waiting on: {}".format(game['waitingId']))
	return commentResult


def sendTipNumberMessages(game, coaches):
	reddit.sendMessage(coaches,
			   'Tip Number',
			   embedTableInMessage("\n\nReply with a number between \
						**1** and **{0}**, inclusive.".format(globals.maxRange)
					       , {'action': 'tip'}))
	messageResult = reddit.getRecentSentMessage()
	game['waitingId'] = messageResult.fullname
	log.debug("Tip number sent, now waiting on: {}".format(game['waitingId']))


def tipResults(game, homeaway,number):
	tipKey = '{}Tip'.format(homeaway)
	if game[tipKey] == '':
		game[tipKey] = number
	else:
		return game, 'Already sent a number', False
	if game['homeTip'] != '' and game['awayTip'] != '':
		game['dirty'] =  True
	return game, 'result time', True

def getHomeAwayString(isHome):
	if isHome:
		return 'home'
	else:
		return 'away'


def reverseHomeAway(homeAway):
	if homeAway == 'home':
		return 'away'
	elif homeAway == 'away':
		return 'home'
	else:
		return None


def getRange(rangeString):
	rangeEnds = re.findall('(\d+)', rangeString)
	if len(rangeEnds) < 2 or len(rangeEnds) > 2:
		return None, None
	return int(rangeEnds[0]), int(rangeEnds[1])


def isGameWaitingOn(game, user, action, messageId):
	log.debug('checking on if we are waiting for {} with action {}'.format(user, action))
	log.debug('waitingAction is {}'.format(game['waitingAction']))
	if game['waitingAction'] == 'tip' and action == 'tip':
		log.debug('I am waiting on tip')
		return None
	if game['waitingAction'] != action:
		log.debug("Not waiting on {}: {}".format(action, game['waitingAction']))
		return "I'm not waiting on a {} for this game, \
		are you sure you replied to the right message?".format(action)

	if (game['waitingOn'] == 'home') != isCoachHome(game, user):
		log.debug("Not waiting on message author's team")
		return "I'm not waiting on a message from you, \
		are you sure you responded to the right message?"

	if game['waitingId'] is not None and game['waitingId'] != messageId:
		log.debug("Not waiting on message \
				id: {} : {}".format(game['waitingId'], messageId))
		return "I'm not waiting on a reply to this message, \
		be sure to respond to my newest message for this game."

	return None


def getCoachString(game, homeAway):
	bldr = []
	for coach in game[homeAway]['coaches']:
		bldr.append("/u/{}".format(coach))
	return " and ".join(bldr)


def getNthWord(number):
	if number == 1:
		return "1st"
	elif number == 2:
		return "2nd"
	else:
		return "{}th".format(number)






def getCurrentPlayString(game):
	if  game['status']['tipped'] == False:
		return "You just won the tip."
	if game['status']['scored']:
		game['status']['scored'] = False
		return "{} just scored".format(game[game['status']['possession']]['name'])
	else:
		return game['play']['playResult']



def getWaitingOnString(game):
	string = "Error, no action"
	if game['waitingAction'] == 'tip':
		waitingOn = []
		if game['homeTip'] == '':
			waiting.append['home']
		if game['awayTip'] == '':
			waiting.append['away']

		string = "Waiting on {} for tip numbers".format(''.join(waitingOn))
	elif game['waitingAction'] == 'defer':
		string = "Waiting on {} for receive/defer".format(game[game['waitingOn']]['name'])
	elif game['waitingAction'] == 'play':
		if game['waitingOn'] == game['status']['possession']:
			string = "Waiting on {} for an offensive play".format(game[game['waitingOn']]['name'])
		else:
			string = "Waiting on {} for a defensive number".format(game[game['waitingOn']]['name'])

	return string


def sendDefensiveNumberMessage(game, mess=None, recpt=None):
	defenseHomeAway = reverseHomeAway(game['status']['possession'])
	log.debug("Sending get defense number message to {}".format(getCoachString(game, defenseHomeAway)))
	if mess is not None:
		reddit.sendMessage(game[game['waitingOn']]['coaches'][0], 'Tip result',
			   embedTableInMessage(mess, {'action': 'play'}))
	else:
		reddit.sendMessage(game[defenseHomeAway]['coaches'],
			   "{} vs {}".format(game['away']['name'], game['home']['name']),
			   embedTableInMessage("{}\n\nReply with a number between **1** and **{}**, inclusive.".format(getCurrentPlayString(game), globals.maxRange)
					       , {'action': 'play'}))

	messageResult = reddit.getRecentSentMessage()
	log.debug('messageResult is {}'.format(messageResult))
	game['waitingId'] = messageResult.fullname
	log.debug("Defensive number sent, now waiting on: {}".format(game['waitingId']))


def extractPlayNumber(message):
	numbers = re.findall('(\d+)', message)
	if len(numbers) < 1:
		log.debug("Couldn't find a number in message")
		return -1, "It looks like you should be sending me a number, \
						but I can't find one in your message."
	if len(numbers) > 1:
		log.debug("Found more than one number")
		return -1, "It looks like you puts more than one number in your message"

	number = int(numbers[0])
	if number < 1 or number > globals.maxRange:
		log.debug("Number out of range: {}".format(number))
		return -1, "I found {}, but that's not a valid number.".format(number)

	return number, None


def setLogGameID(threadId, gameId):
	globals.gameId = gameId
	globals.logGameId = " {}:".format(threadId)


def clearLogGameID():
	globals.gameId = None
	globals.logGameId = ""


def findKeywordInMessage(keywords, message):
	found = []
	for keyword in keywords:
		if isinstance(keyword, list):
			for actualKeyword in keyword:
				if actualKeyword in message:
					found.append(keyword[0])
					break
		else:
			if keyword in message:
				found.append(keyword)

	if len(found) == 0:
		return 'none'
	elif len(found) > 1:
		log.debug("Found multiple keywords: {}".format(', '.join(found)))
		return 'mult'
	else:
		return found[0]


def listSuggestedPlays(game):
	return 'Play'


def buildMessageLink(recipient, subject, content):
	return "https://np.reddit.com/message/compose/?to={}&subject={}&message={}".format(
		recipient,
		subject.replace(" ", "%20"),
		content.replace(" ", "%20")
	)


def addStatRunPass(game, runPass, amount):
	if runPass == 'run':
		addStat(game, 'yardsRushing', amount)
	elif runPass == 'pass':
		addStat(game, 'yardsPassing', amount)
	else:
		log.warning("Error in addStatRunPass, invalid play: {}".format(runPass))


def addStat(game, stat, amount, offenseHomeAway=None):
	if offenseHomeAway is None:
		offenseHomeAway = game['status']['possession']
	log.debug('we are adding {} amount to stat {} for the {} team'.format(amount, stat, offenseHomeAway))
	game[offenseHomeAway][stat] += amount



def isGameOvertime(game):
	return str.startswith(game['status']['halfType'], 'overtime')


def updateGameTimes(game):
	game['playclock'] = database.getGamePlayed(game['dataID'])
	game['dirty'] = database.getGameDeadline(game['dataID'])


def newGameObject(home, away):
	status = {'clock': globals.halfLength, 'half': 1, 'location': -1, 'possession': 'home',
		  'timeouts': {'home': globals.timeouts, 'away': globals.timeouts}, 'requestedTimeout': {'home': 'none', 'away': 'none'}, 'free': False, 'frees': 0, 'freeStatus': None,
		  'halfType': 'normal', 'overtimePossession': None,'scored':False,'wonTip':'','tipped':False}
	tip = {'homeTip':False, 'awayTip':False, 'justTipped':False, 'tipMessage':'','tipped':False}
	score = {'halves': [{'home': 0, 'away': 0}, {'home': 0, 'away': 0}], 'home': 0, 'away': 0}
	play = {'fouled':False,'defensiveNumber':True, 'offensiveNumber':False, 'playResult':'', 'playDesc':''}
	game = {'home': home, 'away': away, 'poss': [], 'status': status, 'score': score, 'errored': 0, 'waitingId': None,
		'waitingAction': 'tip', 'waitingOn': 'away', 'dataID': -1, 'thread': "empty",
		'dirty': False, 'startTime': None, 'location': None, 'station': None, 'playclock': datetime.utcnow() + timedelta(hours=24),
		'deadline': datetime.utcnow() + timedelta(days=10),'isOverTime':False,  'play':play, 'tip':tip }


	return game
