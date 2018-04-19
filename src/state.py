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
	if not game['tip'][tipKey]:
		success = database.saveTipNumber(game['dataID'],number, tipKey)
		if success:
			game['tip'][tipKey] = True
		else:
			return 'could not save this number', False
	else:
		return 'Already sent a number', False
	log.debug('hometip is {} and awaytip is {}'.format(game['tip']['homeTip'], game['tip']['awayTip']))
	if game['tip']['homeTip'] and game['tip']['awayTip']:
		log.debug('Setting dirty to True')
		game['dirty'] = True
		log.debug('game dirty is {} right after update'.format(game['dirty']))
	else:
		return 'You sent {}'.format(number), True
	utils.updateGameThread(game)
	log.debug('game is dirty is {}. this is after updating game thread'.format(game['dirty']))
	return 'result time', True

def setStateOvertime(game, homeAway):
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

	game['play']['onum'] = offenseNumber
	game['play']['dnum'] = defenseNumber
	game['play']['diff'] = difference

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


def getTimeByPlay(game,play):
	offenseNumbers = wiki.getTimeByPlay(game)
	if offenseNumbers is None:
		log.warning("Could not get time result for play: {}".format(play))
		return None

	if play not in offenseNumbers:
		log.warning("play is not in this set of offense numbers")
		return None

	timeObject = offenseNumbers[play]
	log.debug("Time to take off is {}".format(timeObject))
	return timeObject



def updateTime(game, play, result, offenseHomeAway):
	if result == 'FREE':
		return ''
	elif result == 'FREEDONE':
		timeOffClock = 0
	elif play == 'ifoul':
		timeOffClock = globals.ifoulTime
	else:
		timeOffClock = getTimeByPlay(game, play)
	log.debug("time off the clock was {}".format(timeOffClock))



	log.debug("Time off clock: {} : {}".format(game['status']['clock'], timeOffClock))
	game['status']['clock'] -= timeOffClock
	log.debug('clock after subtraction is {}'.format(game['status']['clock']))
	timeMessage = "{} left".format(utils.renderTime(game['status']['clock']))

	if game['status']['clock'] <= 0:
		log.debug("End of half: {}".format(game['status']['half']))
		actualTimeOffClock = timeOffClock + game['status']['clock']
		utils.addStat(game, 'posTime', actualTimeOffClock, offenseHomeAway)
		game['status']['clock'] = 0
		if not game['status']['free']:
			timeMessage = endHalf(game)
			if game['status']['halfType'] != 'end' and game['status']['half'] > 2:
				log.debug('Setting OverTime information')
				game['status']['clock'] = globals.otLength
				game['score']['halves'].append({'home':0,'away':0})
				log.debug('Going to null the tip numbers out and make them all false in the game object.')
				database.nullTipNumbers(game['dataID'])
				game['tip']['homeTip'] = False
				game['tip']['awayTip'] = False
				coaches = [game['home']['coaches'][0], game['away']['coaches'][0]]
				utils.sendTipNumberMessages(game, coaches)
	else:
		actualTimeOffClock = timeOffClock
		utils.addStat(game, 'posTime', actualTimeOffClock, offenseHomeAway)

	if game['status']['clock'] <= 0 and game['status']['halfType'] == 'end':
		return "The play took {} seconds, {}".format(actualTimeOffClock, timeMessage)
	elif game['status']['clock'] <= 0 and game['status']['halfType'] =='overtimeNormal':
		return "The play took {} seconds, {}".format(actualTimeOffClock, timeMessage)
	elif game['status']['clock'] <= 0 and game['status']['halfType'] not in ('end', 'overtimeNormal') and game['status']['free']:
		return "The play took {} seconds, No time left on the clock".format(actualTimeOffClock)
	else:
		return "The play took {} seconds, {}".format(actualTimeOffClock, timeMessage)


def endHalf(game):
	timeMessage = 'Default Message'
	game['status']['clock'] = 0
	if game['status']['half'] == 1:
		timeMessage = "end of the first half"
		game['status']['clock'] =  globals.halfLength
		game['status']['posession'] = utils.reverseHomeAway(game['status']['wonTip'])
		game['status']['waitingAction'] = 'play'
		game['status']['half'] = 2
	else:
		if game['status']['half'] >= 2:
			if game['score']['home'] == game['score']['away']:
				game['status']['tipped'] = False
				game['status']['half'] += 1
				if game['status']['half'] == 3:
					log.debug("Score tied at end of 2nd half, going to overtime")
					timeMessage = "end of regulation. The score is tied, we're going to overtime!"
				else:
					log.debut('Score still tied at the end of OT {}: Going into OT{}'.format(game['status']['half']-1, game['status']['half']))
					timeMessage = 'End of OT number {}, going into OT {}'.format(game['status']['half']-1, game['status']['half'])
				if database.getGameDeadline(game['dataID']) > datetime.utcnow() and 0 == 1:
					game['status']['halfType'] = 'overtimeTime'
				else:
					game['status']['halfType'] = 'overtimeNormal'
				game['waitingAction'] = 'tip'
			else:
				log.debug("End of game")
				if game['score']['home'] > game['score']['away']:
					victor = 'home'
				else:
					victor = 'away'
				timeMessage = "that's the end of the game! {} has won!".format(utils.flair(game[victor]))
				game['status']['halfType'] = 'end'
				game['waitingAction'] = 'end'
				utils.createPostGameThread(game)
				database.endGame(game['thread'])

				try:
					for team in ['home','away']:
						utils.setStatsForSheet(game, team)
				except:
					log.debug('Cannot insert stats for teams with gameid {}'.format(game['dataID']))
				hins, ains = utils.insertStatData(game)

	return timeMessage


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
		result = "FREE"
		if number == -1:
			log.debug("Trying to shoot a free throw play, but didn't have a number")
			resultMessage = numberMessage
			success = False
			return False, resultMessage
		elif number > -1:
			game['status']['frees'] -= 1

			utils.addStat(game,'FTAttempted',1,startingPossessionHomeAway)
			numberResult, diffMessage = getNumberDiffForGame(game, number)
			freeResult = getFreeThrowResult(game,numberResult)


			if freeResult:
				game['play']['result'] = 'Free Made'
				log.debug("Successful Free Throw")
				resultMessage = "The Free throw was successful"
				utils.addStat(game,'FTMade',1,startingPossessionHomeAway)
				scoreFreeThrow(game, startingPossessionHomeAway)
				if game['status']['free'] == '1and1Start':
					game['status']['frees'] = 1
					game['status']['free'] = True
			else:
				game['play']['result'] = 'Free Missed'
				log.debug("failed free throw")
				resultMessage =  "The free throw has cursed you. Suffer."
			if game['status']['frees'] == 0:
				game['status']['free'] = False
				game['waitingAction'] =  'play'
				game['play']['playResult'] = 'freeDone'
				game['freeThrows']['freeType'] = None
				result = "FREEDONE"
			else:
				pass
##			database.clearDefensiveNumber(game['dataID'])
		else:
			resultMessage = "It looks like /]you're trying to get the extra point after a touchdown, but this isn't a valid play"
			success = False
	elif game['status']['ifoul']:
		resultMessage = setFouls(game, 0)
		game['play']['playResult'] = 'fouled'

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
				game['play']['result'] = result['result']
				playResultName = result['result'].lower()
				log.debug('playResultName is {}'.format(playResultName))
				ptf = re.search('2|3', playResultName)
				log.debug("ptf is {}".format(ptf))
				if ptf:
					pointsTriedFor = int(ptf.group(0))
					log.debug("this shot as an attempt for {} points".format(pointsTriedFor))
				if playResultName.lower() in globals.pointResults :
					if 'points' not in result:
						log.warning("Result is a score, but I couldn't find any points")
						resultMessage = "Result of play is a number of points, but something went wrong and I couldn't find what number"
						success = False
					else:
						if playResultName in globals.foulPlays:
							##After this play we will be waiting on the current devensive
							##team since they will have to send a defensive number
							fouled =  True
						points = result['points']
						resultMessage = 'Basket good for {} points.'.format(points)
						if fouled:
							resultMessage = resultMessage + ' AND ONE. Player is fouled.'
						if points ==  2:
							sub2Pt(game, True, fouled)
							game['play']['playDesc'] = '2'
							game['play']['playResult'] = 'made'
							game['status']['scored'] = True
						elif points == 3:
							sub3Pt(game, True, fouled)
							game['play']['playResult'] = 'made'
							game['play']['playDesc'] = '3'
							game['status']['scored'] = True
						log.debug("Result is a gain of {} points".format(points))
				elif playResultName in globals.foulMissPlays:
					log.debug("In foul Miss Plays")
					##get numbers to see how many free thors we will shoot
					setFouls(game, pointsTriedFor)
					resultMessage = 'Fouled on a {0}pt shot. The shot is missed.  Going to shoot {0} freethrows.'.format(pointsTriedFor)
					game['play']['playResult'] = 'fouled'
				elif playResultName in globals.nonShootingFoul:
					##This sets possession in the bonus check
					resultMessage = setFouls(game, 0)
					game['play']['playResult'] = 'fouled'
				elif playResultName in globals.missPlays:
					log.debug('In miss plays')
					game['play']['playResult'] = 'miss'##No need to change who we are waitingon here
					if pointsTriedFor == 2:
						sub2Pt(game, False, False)

					elif pointsTriedFor == 3:
						sub3Pt(game, False, False)
					else:
						return False, "Could not detect a number like we think it should. We must pay with our "
					resultMessage = "Missed a {} point shot.".format(pointsTriedFor)
				elif playResultName in globals.offRebounds:
					game['play']['playResult'] = 'off rebound'
					shotType = utils.coinToss()


					if shotType:
						log.debug('By random choice this was a 2 point shot')
						sub2Pt(game, False, False, True)
					else:
						log.debug('By random choice this was a 3 point shot')
						sub3Pt(game, False, False, True)


					resultMessage = "Missed a shot but got the offensive rebound"
				elif playResultName in globals.turnovers:
					game['play']['playResult'] = 'turnover'
					setTurnovers(game, playResultName.lower())
					if playResultName == "Steal":
						resultMessage = "Hark, a steal"
					else:
						resultMessage = 'Turned the ball over'
				elif playResultName == 'block':
					resultMessage = "the shot was BLOCKED"
					game['play']['playResult'] = 'block'
					setBlock(game, 'block')


				database.clearDefensiveNumber(game['dataID'])
		else:
			resultMessage = "{} isn't a valid play at the moment".format(play)
			success = False
	messages = [resultMessage]
	if resultMessage is not None:
		if game['status']['ifoul']:
			game['status']['ifoul'] = False
			diffMessage = None
			result = None
			timeMessage = updateTime(game, play, result, startingPossessionHomeAway)
		if timeMessage is None:
			timeMessage = updateTime(game, play, result, startingPossessionHomeAway)

		messages.append(timeMessage)
	if diffMessage is not None:
		messages.append(diffMessage)
	log.debug("Finishing execution of play")
	log.debug("We will be waiting on {} for next number".format(game['waitingOn']))
	log.debug("messages: resultMessage: {}, timeMessage:{}, diffMessage:{}".format(resultMessage, timeMessage, diffMessage))
	##determine here if we need to change possession
	changePossession(game)
	game['play']['playResult'] = ''

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
		if fouled:
			log.debug('Going to set foul information for a 3 point shot made with an and one')
			setFouls(game, 1)
	elif not made and not fouled and not off:
		log.debug('Going to add a defensive rebound on a 3 point shot to the other team')
		utils.addStat(game,'defRebound', 1, utils.reverseHomeAway(team))
	elif off:
		utils.addStat(game, 'offRebound',1, team)
	elif fouled and not made:
		log.debug("going to set foul information for an agent ")
		setFouls(game, 3)
	else:
		log.warning("should not be here in the sub3Pt function")



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
		score2Points(game, team)
		utils.addStat(game,'2PtMade',1,team)
		if fouled:
			log.debug('Just scored 2 and going to set 1 foul for the one and one on')
			setFouls(game, 1)
	elif not made and not fouled and not off:
		log.debug('Going to add a defensive rebound on a 2 point shot to the other team')
		utils.addStat(game,'defRebound', 1, utils.reverseHomeAway(team))
	elif off:
		utils.addStat(game, 'offRebound',1,team)
	elif fouled and not made:
		setFouls(game, 2)
		log.debug('Missed a 2 point shot but going to set 2 free throws')
	else:
		log.warning("OOPS. should not be here in sub2Pt")


def setFouls(game,f_type):
	'''
	Pass in f_type which is used to determine if we are doing an after shot or a nonshooting
	foul. If f_type is zero then we will check if we are in the bonus to determine next
	action. Else we will shoot that many f_type number of free throws
	'''
	team = game['status']['possession']
	otherTeam = utils.reverseHomeAway(team)
	if f_type == 0:
		return setBonusFouls(game, team, otherTeam)
	else:
		game['status']['frees'] = f_type
		game['status']['free'] = True
		game[otherTeam]['fouls'] += 1
		game['status']['freeStatus'] = f_type

def technicalFouls(game):
	pass

def setBonusFouls(game, team, otherTeam):
	message = ''
	utils.addStat(game, 'fouls',1, otherTeam)
	otherFouls =  int(game[otherTeam]['fouls'])
	if  globals.singleBonus <= otherFouls < globals.doubleBonus:
		game[team]['bonus'] = 'SB'
		game['status']['free'] = '1and1Start'
		game['status']['frees'] =  1
		game['freeThrows']['freeType'] = '1and1'
		message = 'In the bonus, shooting the one and one. '
		#chagne waiting action and stuff
	elif globals.doubleBonus <= otherFouls:
		game[team]['bonus'] = 'DB'
		game['status']['free'] = True
		game['status']['frees'] =  2
		game['status']['freeType'] = 2
		game['status']['freeStatus'] = 2
		message = 'In the double bonus, shooting two.'
	else:
		message = 'Fouled but not in the bonus. Offense maintains possession. '
		game['status']['fouledOnly'] = True
	if game['status']['ifoul']:
		foulMessage = ['Intentional Foul by the defense. ']
		foulMessage.append(message)
		return ''.join(foulMessage)
	else:
		return message




def changePossession(game):
	log.debug('determing if we need to change possesion.')
	log.debug('the play result is {}'.format(game['play']['playResult']))
	isIn =  game['play']['playResult'] in globals.switchPossessions
	log.debug('is this a switch posession? Well the result is {}'.format(isIn))
	if isIn and not game['status']['free']:
		log.debug('We should be switching possession')
		current = game['status']['possession']
		game['status']['possession'] = utils.reverseHomeAway(current)


def setTurnovers(game,turnover):
	s_turnover =  "{}{}".format(turnover,'s')
	current =  game['status']['possession']
	if turnover == 'steal':
		utils.addStat(game, s_turnover, 1, utils.reverseHomeAway(current))
	utils.addStat(game, 'turnovers', 1, current)


def setBlock(game,turnover):
	current = game['status']['possession']
	utils.addStat(game,'blocks', 1, utils.reverseHomeAway(current))
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
	begRange, endRange =  utils.getRange(values)
	log.debug('Trying to see if {} is between {} and {}'.format(number, begRange, endRange))
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
	return game

def setWaitingOn(game):
	log.debug('going to set waitingOn. It is currently set to {}'.format(game['waitingOn']))
	##use this to set waitingOn. MOvfe all waiting on logic to homeRecord
	current = game['status']['possession']
	other = utils.reverseHomeAway(current)
	log.debug("logging various useful information")
	log.debug("current is {}".format(current))
	log.debug("other is {}".format(other))
	log.debug("just fouled is {}".format(game['play']['fouled']))
	log.debug("shooting free throws is {}".format(game['status']['free']))

	if (game['status']['free'] or game['status']['fouledOnly']) and game['play']['offensiveNumber']:
		##just sent an offensive play and is now shooting a free throw or
		##fouled and possession stays the same.
		game['waitingOn'] = other
		switchDefOff(game)
		game['status']['fouledOnly'] =  False
	elif game['status']['free'] and game['play']['defensiveNumber']:
		##offensive player was fouled and the defending team just
		##sent their number in
		game['waitingOn'] = current
		switchDefOff(game)
	elif game['play']['defensiveNumber']:
		##someone just sent the defnesive number so we are switching
		##waiting on to the offensive player
		switchDefOff(game)
		game['waitingOn'] = current
	elif game['play']['offensiveNumber']:
		switchDefOff(game)
	log.debug('we are currently awiting on {}'.format(game['waitingOn']))
