import logging.handlers
import re
import praw

import reddit
import utils
import wiki
import globals
import database
import state

log = logging.getLogger("bot")


def processMessageNewGame(body, author):
	log.debug("Processing new game message")
	log.debug("User trying to create message is {0}".format(author.lower()))

	if author.lower() not in wiki.admins and author.lower() != 'zenverak':
		log.debug("User /u/{} is not allowed to create games".format(author))
		return "Only admins can start games"

	users = re.findall('(?: /u/)([\w-]*)', body)
	if len(users) < 2:
		log.debug("Could not find an two teams in create game message")
		return "Please resend the message and specify two teams"

	homeCoach = users[0].lower()
	awayCoach = users[1].lower()
	log.debug("Found home/away coaches in message /u/{} vs /u/{}".format(homeCoach, awayCoach))

	i, result = utils.verifyCoaches([homeCoach, awayCoach])

	if result == 'same':
		log.debug("Coaches are on the same team")
		return "You can't list two coaches that are on the same team"

	if result == 'duplicate':
		log.debug("Duplicate coaches")
		return "Both coaches were the same"

	if i == 0 and result == 'team':
		log.debug("Home does not have a team")
		return "The home coach does not have a team"

	if i == 0 and result == 'game':
		log.debug("Home already has a game")
		return "The home coach is already in a game"

	if i == 1 and result == 'team':
		log.debug("Away does not have a team")
		return "The away coach does not have a team"

	if i == 1 and result == 'game':
		log.debug("Away already has a game")
		return "The away coach is already in a game"

	startTime = None
	location = None
	station = None
	homeRecord = None
	awayRecord = None

	for match in re.finditer('(?: )(\w+)(?:=")([^"]*)', body):
		if match.group(1) == "start":
			startTime = match.group(2)
			log.debug("Found start time: {}".format(startTime))
		elif match.group(1) == "location":
			location = match.group(2)
			log.debug("Found location: {}".format(location))
		elif match.group(1) == "station":
			station = match.group(2)
			log.debug("Found station: {}".format(station))
		elif match.group(1) == "homeRecord":
			homeRecord = match.group(2)
			log.debug("Found home record: {}".format(homeRecord))
		elif match.group(1) == "awayRecord":
			awayRecord = match.group(2)
			log.debug("Found away record: {}".format(awayRecord))

	return utils.startGame(homeCoach, awayCoach, startTime, location, station, homeRecord, awayRecord)


def processMessageTip(game, message):
	number, error = utils.extractPlayNumber(message.body)
	if error is not None:
		return False, "Didn't send me a number. Reply to the original message and send me a number this time"
	author = str(message.author).lower()

	log.debug('author is {}'.format(author))
	log.debug('number is {}'.format(number))
	log.debug("Processing tip ball where game is dirty is {}".format(game['dirty']))
	log.debug('is author in {} or {}'.format(game['away']['coaches'], game['home']['coaches']))
	if author in game['away']['coaches']:
		resultMessage, worked = state.tipResults(game, 'away', number)
	elif author in game['home']['coaches']:
		resultMessage, worked = state.tipResults(game, 'home', number)
	else:
		return False,  'ooops'
	log.debug('Now checking if game is dirty and tip off is complete')
	log.debug('Dirty is {}'.format(game['dirty']))
	if game['tip']['awayTip'] and game['tip']['homeTip']:
		awayTip = int(database.getTipById(game['dataID'],'awayTip'))
		homeTip = int(database.getTipById(game['dataID'],'homeTip'))
		botTip = utils.rngNumber()
		tipWinner = utils.getTipWinner(awayTip, homeTip, botTip)
		game['status']['wonTip'] = tipWinner
		game['waitingOn'] =  utils.reverseHomeAway(tipWinner)
		game['status']['possession'] = tipWinner
		game['play']['defensiveNumber'] = True
		game['play']['offensiveNumber'] = False
		log.debug("sending initial defensive play comment to {}".format(game['waitingOn']))
		resultMessage =  "/u/{} has won the tippoff . /u/{} Will get a DM to start the action. \
						\naway tip number: {}\
						\nhome tip number: {}\
						\nbot tip number: {}".format(
						game[tipWinner]['coaches'][0],
						game[game['waitingOn']]['coaches'][0],
						awayTip,
						homeTip,
						botTip
						)

		defMessage = "You lost the tipoff . Please send me a number to start the game getween **1** and **{}**".format(globals.maxRange)
		log.debug('defensive message is {}'.format(defMessage))
		game['dirty'] =  True

		utils.sendDefensiveNumberMessage(game, defMessage)
		game['waitingAction'] = 'play'
		game['tip']['justTipped'] = True

		return True, resultMessage
	return worked, resultMessage


def processMessageDefenseNumber(game, message, author):
	numberMessage = None
	resultMessage = None
	log.debug("Processing defense number message")
	if message.find(globals.intFoul) > -1:
		log.debug('defense will commit an intentional foul')
		game['status']['ifoul'] = True
	else:
		number, resultMessage = utils.extractPlayNumber(message)
	if resultMessage is not None and not game['status']['ifoul']:
		return False, resultMessage
	elif resultMessage is None  and not game['status']['ifoul']:
		log.debug("Saving defense number: {}".format(number))
		database.saveDefensiveNumber(game['dataID'], number)
	else:
		log.debug('saving defesive number as 0 due to an intentional foul')
		database.saveDefensiveNumber(game['dataID'],0)

	timeoutMessage = None
	if message.find("timeout") > -1:
		timeoutMessage = "Defense cannot call timeouts in basketball."
		# log.debug("defense called a timeout.")
		# if game['status']['timeouts'][utils.reverseHomeAway(game['status']['possession'])] > 0:
		# 	game['status']['requestedTimeout'][utils.reverseHomeAway(game['status']['possession'])] = 'requested'
		# 	timeoutMessage = "Timeout requested successfully"
		# else:
		# 	timeoutMessage = "You requested a timeout, but you don't have any left"
	log.debug("offense is currently {}".format(game['play']['offensiveNumber']))

	log.debug("we were waiting on {}".format(game['waitingOn']))
	state.setWaitingOn(game)
	log.debug("we are now waiting on {}".format(game['waitingOn']))
	log.debug("offene is is {}".format(game['play']['offensiveNumber']))
	game['dirty'] = True

	log.debug("Sending offense play comment")
	if  not game['status']['free']:
		resultMessage = "{} has submitted their number. {} you're up\
		.\n\n{}\n\n{} reply with {} and your number. [Play list]({})".format(
			game[utils.reverseHomeAway(game['waitingOn'])]['name'],
			game[game['waitingOn']]['name'],
			utils.getCurrentPlayString(game),
			utils.getCoachString(game, game['waitingOn']),
			utils.listSuggestedPlays(game),
			"https://www.reddit.com/r/TestFakeCBB/wiki/refbot"
			)
	else:
		resultMessage = "{} has submitted their number for your free throw. {} you're up\
		.\n\n{}\n\n{} reply with your free throw number. [Play list]({})".format(
			game[utils.reverseHomeAway(game['waitingOn'])]['name'],
			game[game['waitingOn']]['name'],
			utils.getCurrentPlayString(game),
			utils.getCoachString(game, game['waitingOn']),
			utils.listSuggestedPlays(game),
			"https://www.reddit.com/r/TestFakeCBB/wiki/refbot"
			)
	utils.sendGameComment(game, resultMessage, {'action': 'play'})
	if not game['status']['ifoul']:
		result = ["I've got {} as your number.".format(number)]
	else:
		result = ["You called an intentional foul"]
	if timeoutMessage is not None:
		result.append(timeoutMessage)
	return True, '\n\n'.join(result)


def processMessageOffensePlay(game, message, author):
	log.debug("Processing offense number message")

	if game['status']['ifoul']:
		numberMessage = ''
		number = 0
	else:
		number, numberMessage = utils.extractPlayNumber(message)

	timeoutMessageOffense = None
	if message.find("timeout") > -1:
		log.debug("offense called a timeout")
		if game[game['status']['possession']]['timeouts'] > 0:
			game['status']['requestedTimeout'] = 'requested'
		else:
			timeoutMessageOffense = "The offense requested a timeout, but they don't have any left"

	playOptions = ['chew', 'average', 'push', 'regular']
	if not game['status']['ifoul']:
		playSelected = utils.findKeywordInMessage(playOptions, message)
		play = "default"
		if playSelected == "chew":
			play = "chew"
		elif playSelected == "average":
			play = "average"
		elif playSelected == "push":
			play = "push"
		elif game['status']['free']:
			play = 'free'
		elif playSelected == "mult":
			log.debug("Found multiple plays")
			return False, "I found multiple plays in your message. Please repost it with just the play and number."
		else:
			log.debug("Didn't find any plays")
			return False, "I couldn't find a play in your message Please reply to this one with a play and a number."
	else:
		play = 'ifoul'
		numberMessage = 'intentional foul'
		playSelected = 'ifoul'

	success, resultMessage = state.executePlay(game, play, number, numberMessage)

	if game['status']['requestedTimeout'] == 'used':
		timeoutMessageOffense = "The offense is charged a timeout"
	elif game['status']['requestedTimeout'] == 'requested' and not game['status']['ifoul']:
		timeoutMessageOffense = "The offense requested a timeout, but it was not used"
	elif game['status']['ifoul']:
		timeoutMessageOffense = "The offense request a timeout but it could \
		not be taken due to defense's intentional foul"
	game['status']['requestedTimeout'] = 'none'

	result = [resultMessage]
	if timeoutMessageOffense is not None:
		result.append(timeoutMessageOffense)
	if playSelected != 'default':
		state.setWaitingOn(game)
		game['dirty'] = True
	if game['waitingAction'] == 'play' and playSelected != 'default':
		utils.sendDefensiveNumberMessage(game)
	elif game['waitingAction'] == 'overtime':
		log.debug("Starting overtime, posting coin toss comment")
		message = "Overtime has started! {}, you're away, call **heads** or **tails** in the air.".format(
			utils.getCoachString(game, 'away'))
		comment = utils.sendGameComment(game, message, {'action': 'tip'})
		game['waitingId'] = comment.fullname
		game['waitingAction'] = 'tip'

	return success, utils.embedTableInMessage('\n\n'.join(result), {'action': game['waitingAction']})


def processMessagePauseGame(body):
	log.debug("Processing pause game message")
	threadIds = re.findall('([\da-z]{6})', body)
	if len(threadIds) < 1:
		log.debug("Couldn't find a thread id in message")
		return "Couldn't find a thread id in message"
	log.debug("Found thread id: {}".format(threadIds[0]))

	hours = re.findall('(\d{1,3})', body)
	if len(hours) < 1:
		log.debug("Couldn't find a number of hours in message")
		return "Couldn't find a number of hours in message"
	log.debug("Found hours: {}".format(hours[0]))

	database.pauseGame(threadIds[0], hours[0])

	return "Game {} paused for {} hours".format(threadIds[0], hours[0])


def processMessageAbandonGame(body):
	log.debug("Processing abandon game message")
	threadIds = re.findall('([\da-z]{6})', body)
	if len(threadIds) < 1:
		log.debug("Couldn't find a thread id in message")
		return "Couldn't find a thread id in message"
	log.debug("Found thread id: {}".format(threadIds[0]))

	database.endGame(threadIds[0])

	return "Game {} abandoned".format(threadIds[0])


def processMessageKickGame(body):
	'''
	This isn't kicking but the function that kicks a game, meaning
	that it removes the game from existing
	'''
	log.debug("Processing kick game message")
	numbers = re.findall('(\d+)', body)
	if len(numbers) < 1:
		log.debug("Couldn't find a game id in message")
		return "Couldn't find a game id in message"
	log.debug("Found number: {}".format(str(numbers[0])))
	success = database.clearGameErrored(numbers[0])
	if success:
		log.debug("Kicked game")
		return "Game {} kicked".format(str(numbers[0]))
	else:
		log.debug("Couldn't kick game")
		return "Couldn't kick game {}".format(str(numbers[0]))

def processMessage(message):
	## Determine if comment or dm
	if isinstance(message, praw.models.Message):
		isMessage = True
		log.debug("Processing a message from /u/{} : {}".format(str(message.author), message.id))
	else:
		isMessage = False
		log.debug("Processing a comment from /u/{} : {}".format(str(message.author), message.id))

	response = None
	success = None
	updateWaiting = True
	dataTable = None
	resultMessage = None
	tipped = False

	if message.parent_id is not None and (message.parent_id.startswith("t1") or message.parent_id.startswith("t4")):
		if isMessage:
			parent = reddit.getMessage(message.parent_id[3:])
		else:
			parent = reddit.getComment(message.parent_id[3:])

		if parent is not None and str(parent.author).lower() == globals.ACCOUNT_NAME:

			dataTable = utils.extractTableFromMessage(parent.body)
			if dataTable is not None:
				if 'action' not in dataTable:
					dataTable = None
				else:
					dataTable['source'] = parent.fullname
					log.debug("Found a valid datatable in parent message: {}".format(str(dataTable)))

	body = message.body.lower()
	author = str(message.author)
	game = None
	if dataTable is not None:
		game = utils.getGameByUser(author)
		log.debug('game is {}'.format(game))
		if game is not None:
			utils.setLogGameID(game['thread'], game['dataID'])
			print('the action is {}'.format(dataTable['action']))

			waitingOn = utils.isGameWaitingOn(game, author, dataTable['action'], dataTable['source'])
			log.debug("waitingOn is {}".format(waitingOn))
			if waitingOn is not None:
				response = waitingOn
				success = False
				updateWaiting = False

			elif game['errored']:
				log.debug("Game is errored, skipping")
				response = "This game is currently in an error state, /u/{} has been contacted to take a look".format(globals.OWNER)
				success = False
				updateWaiting = False

			else:
				log.debug('Trying to process tip, offense, or defense')
				##this is where we start the game basically
				if dataTable['action'] == 'tip' and isMessage:
					log.debug('About to process tip message from {}'.format(str(message.author)))
					success, response = processMessageTip(game, message)
					if success:
						game['dirty'] = True
					log.debug("The tip message's success was {} and the message's content reads {}".format(success, response))


				elif dataTable['action'] == 'play' and isMessage:
					success, response = processMessageDefenseNumber(game, body, str(message.author))

				elif dataTable['action'] == 'play' and not isMessage:
					success, response = processMessageOffensePlay(game, body, str(message.author))

		else:
			log.debug("Couldn't get a game for /u/{}".format(author))
	else:
		log.debug("Parsing non-datatable message")
		if "newgame" in body and isMessage:
			response = processMessageNewGame(message.body, str(message.author))
		if "kick" in body and isMessage and str(message.author).lower() == globals.OWNER:
			response = processMessageKickGame(message.body)
		if "pause" in body and isMessage and str(message.author).lower() in wiki.admins:
			response = processMessagePauseGame(message.body)
		if "abandon" in body and isMessage and str(message.author).lower() in wiki.admins:
			response = processMessageAbandonGame(message.body)
	message.mark_read()
	if response is not None:
		if success is not None and not success and dataTable is not None and utils.extractTableFromMessage(response) is None:
			log.debug("Embedding datatable in reply on failure")
			response = utils.embedTableInMessage(response, dataTable)
			if updateWaiting and game is not None:
				game['waitingId'] = 'return'
		log.debug("About to send reply Message")


		if game is not None:
			log.debug("game is not none")
			if game['tip']['justTipped']:
				log.debug('sending the winning tip message to the game thread')
				##send the tip update to the game thread instead of to the last
				## person who sent a tip number
				resultMessage = utils.sendGameCommentAfterTip(game, response)
				game['tip']['justTipped'] =  False
				game['tip']['tipped'] = True
			else:
				resultMessage = reddit.replyMessage(message, response)
		else:
			resultMessage = reddit.replyMessage(message, response)
		log.debug("result of sending reply message was {}".format(resultMessage))
		if resultMessage is None:
			log.warning("Could not send message")
		elif game is not None and game['waitingId'] == 'return':
			game['waitingId'] = resultMessage.fullname
			log.debug('About to send. WaitingID is {} when waitingID was return'.format(game['waitingId']))
			game['dirty'] = True
			log.debug("Message/comment replied, now waiting on: {}".format(game['waitingId']))
	else:
		if isMessage:
			log.debug("Couldn't understand message")
			resultMessage = reddit.replyMessage(message,
								"Could not understand you. Please try again or message /u/zenverak if you need help.")
		if resultMessage is None:
			log.warning("Could not send message")
	if game is not None and game['dirty']:
		log.debug("Game is dirty, updating thread")
		utils.updateGameThread(game)
