import logging.handlers
from datetime import datetime

import wiki
import utils
import globals
import database
import re

log = logging.getLogger("bot")


def scoreForTeam(game, points, homeAway):
	oldScore = game['score'][homeAway]
	game['score'][homeAway] += points
	log.debug("Score for {} changed from {} to {}".format(homeAway, oldScore, game['score'][homeAway]))
	game['score']['halves'][game['status']['half'] - 1][homeAway] += points

def tipResults(game, homeaway,number):
	tipKey = '{}Tip'.format(homeaway)
	if not game[tipKey]:
		success = database.saveTipNumber(game['dataID'],number, tipKey)
		if success:
			game[tipKey] = True
		else:
			return 'could not save this number', False
	else:
		return 'Already sent a number', False
	log.debug('hometip is {} and awaytip is {}'.format(game['homeTip'], game['awayTip']))
	if game['homeTip'] and game['awayTip']:
		log.debug('Setting dirty to True')
		game['dirty'] = True
		log.debug('game dirty is {} right after update'.format(game['dirty']))
	else:
		return 'You sent {}'.format(game[tipKey]), True
	utils.updateGameThread(game)
	log.debug('game is dirty is {}. this is after updating game thread'.format(game['dirty']))
	return 'result time', True

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
	log.debug('Finding where this number, {} ,lies in the dictionary: {}'.format(number, dict))
	for key in dict:
		rangeEnd, rangeStart = utils.getRange(key)
		log.debug('rangeStart is {} and rangeEnd is {}'.format(rangeStart, rangeEnd))
		if rangeStart is None:
			log.warning("Could not extract range: {}".format(key))
			continue

		if rangeStart <= number <= rangeEnd:
			log.debug('found the dict[key] and it is {}'.format(dict[key]))
			return dict[key]

	log.warning("Could not find number in dict")
	return None


def getPlayResult(game, play, number):
	log.debug("Get Wiki data for play {}".format(play))
	playDict = wiki.getPlay(play)
	if playDict is None:
		log.warning("{} is not a valid play".format(play))
		return None
	log.debug("Getting play result for: {}".format(play))
	if play in globals.offPlays:
		offense = game[game['status']['possession']]['offense']
		defense = game[utils.reverseHomeAway(game['status']['possession'])]['defense']
		log.debug("Movement play offense, defense: {} : {}".format(offense, defense))
		playMajorRange = playDict[offense][defense]
	elif play == 'freeThrows':
		pass

	else:
		playMajorRange = playDict

	return findNumberInRangeDict(number, playMajorRange)


def getTimeByPlay(play, result):
	timePlay = wiki.getTimeByPlay(play)
	if timePlay is None:
		log.warning("Could not get time result for play: {}".format(play))
		return None

	if result not in timePlay:
		log.warning("Could not get result in timePlay: {} : {}".format(play, result))
		return None

	timeObject = timePlay[result]



def updateTime(game, play, result, offenseHomeAway):

	timeOffClock = getTimeByPlay(play, result, yards)

	if result in ["gain", "kneel"]:
		if game['status']['requestedTimeout'][offenseHomeAway] == 'requested':
			log.debug("Using offensive timeout")
			game['status']['requestedTimeout'][offenseHomeAway] = 'used'
			game['status']['timeouts'][offenseHomeAway] -= 1
		elif game['status']['requestedTimeout'][utils.reverseHomeAway(offenseHomeAway)] == 'requested':
			log.debug("Using defensive timeout")
			game['status']['requestedTimeout'][utils.reverseHomeAway(offenseHomeAway)] = 'used'
			game['status']['timeouts'][utils.reverseHomeAway(offenseHomeAway)] -= 1

	log.debug("Time off clock: {} : {}".format(game['status']['clock'], timeOffClock))

	game['status']['clock'] -= timeOffClock
	timeMessage = "{} left".format(utils.renderTime(game['status']['clock']))

	if game['status']['clock'] < 0:
		log.debug("End of half: {}".format(game['status']['half']))
		actualTimeOffClock = timeOffClock + game['status']['clock']
		if game['status']['half'] == 1:
			timeMessage = "end of the first half"
			game['status']['clock'] =  globals.halfLength
			game['status']['posession'] = utils.reverseHomeAway(game['status']['wonTip'])
			game['status']['waitingAction'] = 'play'
		else:
			if game['status']['half'] == 2:
				if game['score']['home'] == game['score']['away']:
					log.debug("Score tied at end of 2nd half, going to overtime")
					timeMessage = "end of regulation. The score is tied, we're going to overtime!"
					if database.getGameDeadline(game['dataID']) > datetime.utcnow():
						game['status']['halfType'] = 'overtimeTime'
					else:
						game['status']['halfType'] = 'overtimeNormal'
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
	fouled = False
	log.debug("starting to execute Play with play being {} and number being {}".format(play, number))
	if game['status']['free'] != False:
		if number == -1:
			log.debug("Trying to shoot a free throw play, but didn't have a number")
			resultMessage = numberMessage
			success = False
		elif number > -1:
			game['status']['frees'] -= 1

			utils.addStat(game,'FTAttempted',1,startingPossessionHomeAway)
			numberResult, diffMessage = getNumberDiffForGame(game, number)
			freeResult = getFreeThrowResult(game,numberResult)

			if freeResult:
				log.debug("Successful Free Throw")
				resultMessage = "The Free throw was successful"
				utils.addStat(game,'FTMade',1,startingPossessionHomeAway)
				scoreFreeThrow(game, startingPossessionHomeAway)
				if game['status']['free'] == '1and1Start':
					game['status']['frees'] = 1
					game['status']['free'] = True
			else:
				log.debug("failed free throw")
				resultMessage =  "The free throw has cursed you. Suffer."
			if game['status']['frees'] == 0:
				game['status']['free'] = False
				game['waitingAction'] =  'play'
				game['possession'] = utils.reverseHomeAway(startingPossessionHomeAway)
			else:
				game['status']['waitingOn'] = utils.reverseHomeAway(startingPossessionHomeAway)
			database.clearDefensiveNumber(game['dataID'])
		else:
			resultMessage = "It looks like /]you're trying to get the extra point after a touchdown, but this isn't a valid play"
			success = False
	else:
		if play in globals.offPlays:
			if number == -1:
				log.debug("Trying to execute a normal play, but didn't have a number")
				resultMessage = numberMessage
				success = False
			else:
				numberResult, diffMessage = getNumberDiffForGame(game, number)
				log.debug("numberResult was {}".format(numberResult))
				log.debug("Executing normal play: {}".format(play))
				result = getPlayResult(game, play, numberResult)
				playResultName = result['result']
				ptf = re.search('2|3', playResultName)
				if ptf:
					pointsTriedFor = int(ptf.group(0))
				if playResultName in globals.pointResults :
					if 'points' not in result:
						log.warning("Result is a score, but I couldn't find any points")
						resultMessage = "Result of play is a number of points, but something went wrong and I couldn't find what number"
						success = False
					else:
						if playResultName in globals.foulPlays:
							##After this play we will be waiting on the current devensive
							##team since they will have to send a defensive number
							fouled =  True
						else:
							game['status']['possession'] = utils.reverseHomeAway(game['status']['possession'])

						points = result['points']
						if fouled:
							resultMessage = resultMessage + ' AND ONE. Player is fouled.'
						resultMessage = 'Basket good for {} points.'.format(points)
						if points ==  2:
							sub2Pt(game, True, fouled)
							game['status']['playResult'] = '2'
							game['status']['scored'] = True
						elif points == 3:
							sub3Pt(game, True, fouled)
							game['status']['playResult'] = '3'
							game['status']['scored'] = True
						log.debug("Result is a gain of {} points".format(points))
				elif playResultName in globals.foulMissPlays:
					##get numbers to see how many free thors we will shoot
					setFouls(game, pointsTriedFor)
					resultMessage = 'Going to shoot {} free throws.'.format(num)
					game['status']['playresult'] = 'Missed a {} point shot but got fouled.'.format(pointsTriedFor)
					foulsAfter(game)
				elif playResultName in globals.nonShootingFoul:
					##This sets possession in the bonus check
					resultMessage = setFouls(game, 0)
				elif playResultName in globals.missPlays:
					##No need to change who we are waitingon here
					if pointsTriedFor == '2':
						sub2Pt(game, False, False, 0)
						game['status']['playResult'] =  'Missed a 2 point bucket'
					else:
						sub3Pt(game, False, False, 0)
						game['status']['playResult'] =  'Missed a 3 point bucket'
					resultMessage = "Missed a {} point shot.".format(pointsTriedFor)
				elif playResultName in globals.offRebound:
					game['waitingOn'] = utils.reverseHomeAway(game['waitingOn'])
					shotType = utils.coinToss()
					if shotType:
						sub2Pt(game, False, False, True)
					else:
						sub3Pt(game, False, False, True)


					resultMessage = "Missed a shot but got the offensive rebound"
				elif playResultName in globals.turnovers:
					setTurnovers(game, playResultName.lower())
				elif playResultName == 'Block':
					setBlock(game, 'block')
				setWaitingOn(game)

				database.clearDefensiveNumber(game['dataID'])
		else:
			resultMessage = "{} isn't a valid play at the moment".format(play)
			success = False
	messages = [resultMessage]
	if actualResult is not None:
		if timeMessage is None:
			timeMessage = updateTime(game, play)
		messages.append(timeMessage)
	if diffMessage is None:
		messages.append(diffMessage)
	log.debug("Finishing execution of play")
	log.debug("We will be waiting on {} for next number".format(game['waitingOn']))
	log.debug("messages: resultMessage: {}, timeMessage:{}, diffMessage:{}".format(resultMessage, timeMessage, diffMessage))
	return success, '\n\n'.join(messages)


def sub3Pt(game, made, fouled, off=False):
	'''
	This function is used for all three point type plays. If a 3 point is missed then it
	only adds to the stat of attepmts. If it is made then it adds the score and then
	adds 3 point made and 3 total points to score. if fouled, then f_type is sent
	'''
	team = game['status']['possession']
	utils.addStat(game,'3PtAttempted',1,team)
	if made:
		score3Points(game, team)
		utils.addStat(game,'3PtMade',1, team)
	if not made and not fouled:
		utils.addStat(game,'defRebound', 1, utils.reverseHomeAway(team))
	if off:
		utils.addStat(game, 'offRebound',1, team)
	if fouled:
		setFouls(game, 3)



def sub2Pt(game, made, fouled, off=False):
	'''
	This function is used for all three point type plays. If a 2 point is missed then it
	only adds to the stat of attepmts. If it is made then it adds the score and then
	adds 2 point made and 2 total points to score.
	'''
	team = game['status']['possession']
	utils.addStat(game,'2PtAttempted',1,team)
	##if the shot was made
	if made:
		scoreTwoPoints(game, team)
		utils.addStat(game,'2PtMade',1,team)
	if not made and not fouled:
		utils.addState(game,'defRebound', 1, utils.reverseHomeAway(team))
	if off:
		utils.addStat(game, 'offRebound',1,team)
	if fouled:
		setFouls(game, 2)
		foulsAfter(game)


def setFouls(game,f_type):
	'''
	Pass in f_type which is used to determine if we are doing an after shot or a nonshooting
	foul. If f_type is zero then we will check if we are in the bonus to determine next
	action. Else we will shoot that many f_type number of free throws
	'''
	team = game['status']['possession']
	otherTeam = utils.reverseHomeAway(team)
	game[otherTeam]['fouls'] += 1
	if f_type == 0:
		return setBonus(game, team, otherTeam)
	else:
		game['status']['frees'] = f_type
		game['status']['free'] = True
		game[otherTeam]['fouls'] += 1


def setBonusFouls(game, team, otherTeam):
	otherFouls =  int(game[otherTeam]['fouls'])
	if  globals.singleBonus <= otherFouls <= globals.doubleBonus:
		game[team]['bonus'] = 'SB'
		game['status']['free'] = '1and1Start'
		game['status']['frees'] =  1
		return 'In the bonus, shooting the one and one.'
		#chagne waiting action and stuff
		foulsAfter(game)
	elif globals.doubleBonus <= otherFouls:
		game[team]['bonus'] = 'DB'
		game['status']['free'] = True
		game['status']['frees'] =  2
		foulsAfter(game)
		return 'In the double bonus, shooting two.'
	else:
		return 'Fouled but not in the bonus. Offense maintains possession'



def changePossession(game):
	current = game['status']['possession']
	game['status']['possession'] = utils.reverseHomeAway(current)


def foulsAfter(game):
	game['waitingOn'] = utils.reverseHomeAway(game['waitingOn'])
#	game['waitingAction'] = 'free'


def setTurnovers(game,turnover):

	game[startingPossessionHomeAway]['turnovers'] += 1
	game[utils.reverseHomeAway(startingPossessionHomeAway)][turnover] += 1
	game['status']['possession'] = utils.reverseHomeAway(startingPossessionHomeAway)


def setBlock(game,turnover):
	game[utils.reverseHomeAway(startingPossessionHomeAway)][turnover] += 1
	game['status']['possession'] = utils.reverseHomeAway(startingPossessionHomeAway)
	shotType = utils.coinToss()
	if shotType:
		sub2Pt(game, False, False)
	else:
		sub3Pt(game, False, False)


def getFreeThrowResult(game,number):
	freeThrowDict = wiki.getPlay('freeThrows')
	if game['location'] == 'neutral':
		values = freeThrowDict['neutral']
	else:
		team = game['status']['possession']
		values = freeThrowDict[team]
	endRange, begRange =  utils.getRange(values)
	if begRange <= number <= endRange:
		return True
	else:
		return False

def switchDefOff(game):
	if game['play']['defensiveNumber']:
		game['play']['defensiveNumber'] = False
		game['play']['offensiveNumber'] =  True
	else:
		game['play']['defensiveNumber'] = True
		game['play']['offensiveNumber'] =  False

def setWaitingOn(game):
	log.debug('going to set waitingOn. It is currently set to {}'.format(game['waitingOn']))
	##use this to set waitingOn. MOvfe all waiting on logic to homeRecord
	current = game['status']['possession']
	other = utils.reverseHomeAway(current)
	if game['play']['fouled']:
		game['waitingOn'] = other
		switchDefOff(game)
	elif game['status']['free']:
		game['waitingOn'] = other
	elif game['play']['defensiveNumber']:
		switchDefOff(game)
		game['waitingOn'] = current
	elif game['play']['offensiveNumber']:
		switchDefOff(game)
	log.debug('we are currently awiting on {}'.format(game['waitingOn']))
