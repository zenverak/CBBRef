import logging.handlers
from datetime import datetime

import wiki
import utils
import globals
import database

log = logging.getLogger("bot")


def scoreForTeam(game, points, homeAway):
	oldScore = game['score'][homeAway]
	game['score'][homeAway] += points
	log.debug("Score for {} changed from {} to {}".format(homeAway, oldScore, game['score'][homeAway]))
	game['score']['halves'][game['status']['half'] - 1][homeAway] += points
	game[homeAway]['halves'][game['status']['half'] - 1][homeAway] += points

def tipResults(game, homeaway,number):
	tipKey = '{}Tip'.format(homeaway)
	if not game[tipKey]:
		database.saveTipNumber(game['dataID'],number, tipKey)
		game[tipKey] = True
	else:
		return game, 'Already sent a number', False
	if game['homeTip']  and game['awayTip']:
		game['dirty'] =  True
	utils.updateGameThread(game)
	return game, 'result time', True

def setStateOvertimeDrive(game, homeAway):
	if homeAway not in ['home', 'away']:
		log.warning("Bad homeAway in setStateOvertimeDrive: {}".format(homeAway))
		return
	if game['status']['overtimePossession'] is None:
		game['status']['overtimePossession'] = 1

	setStateTouchback(game, homeAway)
	game['status']['location'] = 75
	game['waitingOn'] = homeAway


def score3Points(game, homeAway):
	scoreForTeam(game, 3, homeAway)


def score2Points(game, homeAway):
	scoreForTeam(game, 2, homeAway)


def scoreFreeThrow(game, homeAway):
	scoreForTeam(game, 1, homeAway)



def getNumberDiffForGame(game, offenseNumber):
	defenseNumber = database.getDefensiveNumber(game['dataID'])
	if defenseNumber is None:
		log.warning("Something went wrong, couldn't get a defensive number for that game")
		return -1

	straightDiff = abs(offenseNumber - defenseNumber)
	aroundRightDiff = abs(abs(globals.maxRange-offenseNumber) + defenseNumber)
	aroundLeftDiff = abs(offenseNumber + abs(globals.maxRange-defenseNumber))

	difference = min([straightDiff, aroundRightDiff, aroundLeftDiff])

	numberMessage = "Offense: {}\n\nDefense: {}\n\nDifference: {}".format(offenseNumber, defenseNumber, difference)
	log.debug("Offense: {} Defense: {} Result: {}".format(offenseNumber, defenseNumber, difference))

	return difference, numberMessage


def findNumberInRangeDict(number, dict):
	for key in dict:
		rangeStart, rangeEnd = utils.getRange(key)
		if rangeStart is None:
			log.warning("Could not extract range: {}".format(key))
			continue

		if rangeStart <= number <= rangeEnd:
			return dict[key]

	log.warning("Could not find number in dict")
	return None





def getPlayResult(game, play, number):
	playDict = wiki.getPlay(play)
	if playDict is None:
		log.warning("{} is not a valid play".format(play))
		return None
	log.debug("Getting play result for: {}".format(play))
	if play in globals.movementPlays:
		offense = game[game['status']['possession']]['offense']
		defense = game[utils.reverseHomeAway(game['status']['possession'])]['defense']
		log.debug("Movement play offense, defense: {} : {}".format(offense, defense))
		playMajorRange = playDict[offense][defense]
	else:
		playMajorRange = playDict

	playMinorRange = findNumberInRangeDict(100 - game['status']['location'], playMajorRange)
	return findNumberInRangeDict(number, playMinorRange)


def getTimeByPlay(play, result):
	timePlay = wiki.getTimeByPlay(play)
	if timePlay is None:
		log.warning("Could not get time result for play: {}".format(play))
		return None

	if result not in timePlay:
		log.warning("Could not get result in timePlay: {} : {}".format(play, result))
		return None

	timeObject = timePlay[result]
	if result == "gain":
		closestObject = None
		currentDifference = 100
		for yardObject in timeObject:
			difference = abs(yardObject['yards'] - yards)
			if difference < currentDifference:
				currentDifference = difference
				closestObject = yardObject

		if closestObject is None:
			log.warning("Could not get any yardObject")
			return None

		log.debug("Found a valid time object in gain, returning: {}".format(closestObject['time']))
		return closestObject['time']

	else:
		log.debug("Found a valid time object in {}, returning: {}".format(result, timeObject['time']))
		return timeObject['time']


def updateTime(game, play, result, yards, offenseHomeAway):
	if result in ['touchdown', 'touchback']:
		actualResult = "gain"
	else:
		actualResult = result
	if result == 'spike':
		timeOffClock = 3
	else:
		if result == 'kneel':
			timeOffClock = 1
		else:
			timeOffClock = getTimeByPlay(play, actualResult, yards)

		if result in ["gain", "kneel"]:
			if game['status']['requestedTimeout'][offenseHomeAway] == 'requested':
				log.debug("Using offensive timeout")
				game['status']['requestedTimeout'][offenseHomeAway] = 'used'
				game['status']['timeouts'][offenseHomeAway] -= 1
			elif game['status']['requestedTimeout'][utils.reverseHomeAway(offenseHomeAway)] == 'requested':
				log.debug("Using defensive timeout")
				game['status']['requestedTimeout'][utils.reverseHomeAway(offenseHomeAway)] = 'used'
				game['status']['timeouts'][utils.reverseHomeAway(offenseHomeAway)] -= 1
			else:
				if result == 'kneel':
					timeOffClock += 39
				else:
					timeOffClock += getTimeAfterForOffense(game, offenseHomeAway)
		log.debug("Time off clock: {} : {}".format(game['status']['clock'], timeOffClock))

	game['status']['clock'] -= timeOffClock
	timeMessage = "{} left".format(utils.renderTime(game['status']['clock']))

	if game['status']['clock'] < 0:
		log.debug("End of half: {}".format(game['status']['half']))
		actualTimeOffClock = timeOffClock + game['status']['clock']
		if game['status']['half'] == 1:
			timeMessage = "end of the first half"
		else:
			if game['status']['quarter'] == 4:
				if game['score']['home'] == game['score']['away']:
					log.debug("Score tied at end of 4th, going to overtime")
					timeMessage = "end of regulation. The score is tied, we're going to overtime!"
					if database.getGameDeadline(game['dataID']) > datetime.utcnow():
						game['status']['quarterType'] = 'overtimeTime'
					else:
						game['status']['quarterType'] = 'overtimeNormal'
					game['waitingAction'] = 'overtime'
				else:
					log.debug("End of game")
					if game['score']['home'] > game['score']['away']:
						victor = 'home'
					else:
						victor = 'away'
					timeMessage = "that's the end of the game! {} has won!".format(utils.flair(game[victor]))
					game['status']['halfType'] = 'end'
				game['status']['clock'] = 0
				game['waitingAction'] = 'end'
			else:
				if game['status']['half'] == 2:
					log.debug("End of half")
					timeMessage = "end of the first half"

				setStateTouchback(game, game['receivingNext'])
				game['receivingNext'] = utils.reverseHomeAway(game['receivingNext'])
				game['status']['timeouts'] = {'home': 3, 'away': 3}

		if game['status']['quarterType'] != 'end':
			game['status']['half'] += 1
			game['status']['clock'] = globals.quarterLength
	else:
		actualTimeOffClock = timeOffClock

	utils.addStat(game, 'posTime', actualTimeOffClock, offenseHomeAway)

	return "The play took {} seconds, {}".format(timeOffClock, timeMessage)



def executePlay(game, play, number, numberMessage):
	startingPossessionHomeAway = game['status']['possession']
	actualResult = None
	resultMessage = "Something went wrong, I should never have reached this"
	diffMessage = None
	success = True
	timeMessage = None
	if game['status']['free']:
		if number == -1:
			log.debug("Trying to shoot a free throw play, but didn't have a number")
			resultMessage = numberMessage
			success = False

		elif number > -1:
			game['status']['frees'] -= 1
			if game['status']['frees'] == 0:
				game['status']['free'] = False
			utils.addStat(game,'FTAttempted',1,startingPossessionHomeAway)
			numberResult, diffMessage = getNumberDiffForGame(game, number)


			if result['result'] == 'free':
				log.debug("Successful Free Throw")
				resultMessage = "The Free throw was successful"
				utils.addStat(game,'FTMade',1,startingPossessionHomeAway)
				scoreFreeThrow(game, startingPossessionHomeAway)
			else:
				log.debug("failed free throw")
				resultMessage =  "The free throw has cursed you. Suffer."


			database.clearDefensiveNumber(game['dataID'])

		else:
			resultMessage = "It looks like /]you're trying to get the extra point after a touchdown, but this isn't a valid play"
			success = False
	else:
		if play in globals.scorePlays:
			if number == -1:
				log.debug("Trying to execute a normal play, but didn't have a number")
				resultMessage = numberMessage
				success = False

			else:
				numberResult, diffMessage = getNumberDiffForGame(game, number)

				log.debug("Executing normal play: {}".format(play))
				result = getPlayResult(game, play, numberResult)
				if result['result'] == 'score':
					if 'points' not in result:
						log.warning("Result is a score, but I couldn't find any points")
						resultMessage = "Result of play is a number of points, but something went wrong and I couldn't find what number"
						success = False
					else:
						points = result['points']
						if points ==  2:
							scoreTwoPoints(game, startingPossessionHomeAway)
							utils.addStat(game,'2PtAttempted',1,startingPossessionHomeAway)
							utils.addStat(game,'2PtMade',1,startingPossessionHomeAway)
						elif points == 3:
							score3Points(game, startingPossessionHomeAway)
							utils.addStat(game,'3PtAttempted',1,startingPossessionHomeAway)
							utils.addStat(game,'3PtMade',1,startingPossessionHomeAway)
						log.debug("Result is a gain of {} points".format(result['points']))


				if success and play == 'fieldGoal':
					utils.addStat(game, 'fieldGoalsAttempted', 1)

				database.clearDefensiveNumber(game['dataID'])

		elif play in globals.timePlays:
			pass

		else:
			resultMessage = "{} isn't a valid play at the moment".format(play)
			success = False

	messages = [resultMessage]
	if actualResult is not None:
		if timeMessage is not None:
			timeMessage = updateTime(game, play, actualResult, yards, startingPossessionHomeAway)

		messages.append(timeMessage)

	if diffMessage is None:
		messages.append(diffMessage)

	return success, '\n\n'.join(messages)
