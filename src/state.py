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
	game['score']['quarters'][game['status']['quarter'] - 1][homeAway] += points
	game[homeAway]['quarters'][game['status']['quarter'] - 1][homeAway] += points



def setStateOvertimeDrive(game, homeAway):
	if homeAway not in ['home', 'away']:
		log.warning("Bad homeAway in setStateOvertimeDrive: {}".format(homeAway))
		return
	if game['status']['overtimePossession'] is None:
		game['status']['overtimePossession'] = 1

	setStateTouchback(game, homeAway)
	game['status']['location'] = 75
	game['waitingOn'] = homeAway


def score3Point(game, homeAway):
	scoreForTeam(game, 3, homeAway)


def scoreTwoPoint(game, homeAway):
	scoreForTeam(game, 2, homeAway)


def scoreFreeThrow(game, homeAway):
	scoreForTeam(game, 1, homeAway)



def getNumberDiffForGame(game, offenseNumber):
	defenseNumber = database.getDefensiveNumber(game['dataID'])
	if defenseNumber is None:
		log.warning("Something went wrong, couldn't get a defensive number for that game")
		return -1

	straightDiff = abs(offenseNumber - defenseNumber)
	aroundRightDiff = abs(abs(1000-offenseNumber) + defenseNumber)
	aroundLeftDiff = abs(offenseNumber + abs(1000-defenseNumber))

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


def getTimeByPlay(play, result, yards):
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
	if game['status']['conversion']:
		if play in globals.conversionPlays:
			if number == -1:
				log.debug("Trying to execute a normal play, but didn't have a number")
				resultMessage = numberMessage
				success = False

			else:
				numberResult, diffMessage = getNumberDiffForGame(game, number)


				if result['result'] == 'pat':
					log.debug("Successful PAT")
					resultMessage = "The PAT was successful"
					scorePAT(game, game['status']['possession'])
					if utils.isGameOvertime(game):
						timeMessage = overtimeTurnover(game)
					else:
						setStateTouchback(game, utils.reverseHomeAway(game['status']['possession']))

				database.clearDefensiveNumber(game['dataID'])

		else:
			resultMessage = "It looks like /]you're trying to get the extra point after a touchdown, but this isn't a valid play"
			success = False
	else:
		if play in globals.normalPlays:
			if number == -1:
				log.debug("Trying to execute a normal play, but didn't have a number")
				resultMessage = numberMessage
				success = False

			else:
				numberResult, diffMessage = getNumberDiffForGame(game, number)

				log.debug("Executing normal play: {}".format(play))
				result = getPlayResult(game, play, numberResult)
				if result['result'] == 'gain':
					if 'yards' not in result:
						log.warning("Result is a gain, but I couldn't find any yards")
						resultMessage = "Result of play is a number of yards, but something went wrong and I couldn't find what number"
						success = False
					else:
						log.debug("Result is a gain of {} yards".format(result['yards']))
						gainResult, yards, resultMessage = executeGain(game, play, result['yards'])
						if gainResult != "error":
							if yards is not None:
								actualResult = gainResult
						else:
							success = False

				if success and play == 'fieldGoal':
					utils.addStat(game, 'fieldGoalsAttempted', 1)

				database.clearDefensiveNumber(game['dataID'])

		elif play in globals.timePlays:
			if play == 'kneel':
				log.debug("Running kneel play")
				actualResult = "kneel"
				game['status']['down'] += 1
				if game['status']['down'] > 4:
					log.debug("Turnover on downs")
					if utils.isGameOvertime(game):
						timeMessage = overtimeTurnover(game)
					else:
						turnover(game)
					resultMessage = "Turnover on downs"
				else:
					resultMessage = "The quarterback takes a knee"

			elif play == 'spike':
				log.debug("Running spike play")
				actualResult = "spike"
				game['status']['down'] += 1
				if game['status']['down'] > 4:
					log.debug("Turnover on downs")
					if utils.isGameOvertime(game):
						timeMessage = overtimeTurnover(game)
					else:
						turnover(game)
					resultMessage = "Turnover on downs"
				else:
					resultMessage = "The quarterback spikes the ball"

		else:
			resultMessage = "{} isn't a valid play at the moment".format(play)
			success = False

	messages = [resultMessage]
	if actualResult is not None:
		if timeMessage is not None:
			timeMessage = updateTime(game, play, actualResult, yards, startingPossessionHomeAway)

		messages.append(timeMessage)

	if diffMessage is not None:
		messages.append(diffMessage)

	return success, '\n\n'.join(messages)
