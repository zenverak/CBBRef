import sqlite3
from datetime import datetime


dbConn = None

def init():
    global dbConn
    dbConn =  sqlite3.connect('database.db')

init()
null = 'null'
false = False
true = True
stats = {'away': {'2PtAttempted': 17, '2PtMade': 6, '3PtAttempted': 5, '3PtMade': 2, 'FTAttempted': 7, 'FTMade': 5, 'blocks': 0, 'bonus': 'NN', 'coaches': ['jacobguo95', 'jacobguo95'], 'defDiffs': [315, 118, 399, 78, 56, 192, 142, 36, 264, 108, 393, 295, 239, 189, 444, 128, 90, 0, 499, 437, 307, 168, 259, 322, 201, 31, 379, 97, 479, 58, 181, 263, 23, 205, 7, 499, 355, 264, 297, 288, 274, 110, 91], 'defRebound': 6, 'defense': 'presspress', 'fouls': 19, 'name': 'BYU', 'offDiffs': [328, 8, 396, 245, 192, 500, 439, 279, 236, 343, 22, 493, 75, 345, 99, 435, 12, 236, 108, 295, 497, 417, 432, 91, 381, 484, 422, 396, 156, 374, 267, 236, 377, 277, 153, 329], 'offRebound': 1, 'offense': 'attack the rimattack the rim', 'playclockPenalties': 2, 'posTime': 542, 'possessions': 30, 'record': 'nullnull', 'steals': 1, 'tag': 'byubyu', 'timeouts': 8, 'turnovers': 3}, 'dataID': 68, 'deadline': '2018-05-24 21:01:49.034607', 'dirty': False, 'errored': 0, 'freeThrows': {'freeType': 'null'}, 'home': {'2PtAttempted': 17, '2PtMade': 11, '3PtAttempted': 3, '3PtMade': 1, 'FTAttempted': 16, 'FTMade': 12, 'blocks': 1, 'bonus': 'NDB', 'coaches': ['kingkoch32', 'kingkoch32'], 'defDiffs': [328, 8, 396, 245, 192, 500, 439, 279, 236, 343, 22, 493, 75, 345, 99, 435, 12, 236, 108, 295, 497, 417, 432, 91, 381, 484, 422, 396, 156, 374, 267, 236, 377, 277, 153, 329], 'defRebound': 13, 'defense': 'manman', 'fouls': 7, 'name': 'Minnesota', 'offDiffs': [315, 118, 399, 78, 56, 192, 142, 36, 264, 108, 393, 295, 239, 189, 444, 128, 90, 0, 499, 437, 307, 168, 259, 322, 201, 31, 379, 97, 479, 58, 181, 263, 23, 205, 7, 499, 355, 264, 297, 288, 274, 110, 91], 'offRebound': 2, 'offense': 'attack the rimattack the rim', 'playclockPenalties': 1, 'posTime': 661, 'possessions': 26, 'record': 'nullnull', 'steals': 2, 'tag': 'minnesotaminnesota', 'timeouts': 8, 'turnovers': 2}, 'isOverTime': False, 'location': 'Williams Arena', 'neutral': True, 'play': {'dcoach': 'kingkoch32', 'defensiveNumber': False, 'diff': 497, 'dnum': 857, 'fouled': False, 'ocoach': 'jacobguo95', 'offensisiveNumber': False, 'offensiveNumber': True, 'onum': 360, 'playDesc': '2', 'playMessage': 'chew 360', 'playResult': 'made', 'playType': 'chew', 'result': 'stealDunk'}, 'playclock': '2018-05-17 19:54:56', 'poss': [], 'score': {'away': 23, 'halves': [{'away': 8, 'home': 16}, {'away': 15, 'home': 22}], 'home': 38}, 'startTime': '4:32:919 AM', 'station': 'null', 'status': {'changePosWaitCheck': True, 'clock': 0, 'endBoth': False, 'forfeit': False, 'fouledOnly': False, 'free': False, 'freeStatus': 2, 'freeType': 2, 'frees': 0, 'half': 2, 'halfType': 'end', 'ifoul': False, 'location': -1, 'overtimePossession': 'null', 'possession': 'home', 'requestedTimeout': 'null', 'scored': False, 'sendDef': False, 'techFoul': False, 'tipped': False, 'wonTip': 'away'}, 'thread': '8jfum1', 'tip': {'awayTip': True, 'homeTip': True, 'justTipped': False, 'tipMessage': '', 'tipped': True}, 'waitingAction': 'end', 'waitingId': 't1_dz3bh6m', 'waitingOn': 'home'}
def _setStatsData(game, homeAway):
	stats = ['name', '3PtAttempted', '3PtMade', 'FTAttempted','FTMade','turnovers','steals','offRebound','defRebound','fouls','posTime','blocks','possessions']
	data = {'dataID': game['dataID']}
	for stat in stats:
		data[stat] = game[homeAway][stat]
	totShots = game[homeAway]['2PtAttempted'] + game[homeAway]['3PtAttempted']
	totMade =  game[homeAway]['2PtMade'] + game[homeAway]['3PtMade']
	data['totShots'] = totShots
	data['totMade'] = totMade
	winner = getWinner(game)
	if winner == homeAway:
		win = 1
	else:
		win = 0
	data['win'] = win
	other = reverseHomeAway(homeAway)
	offDiffAve = _percentStat(game[homeAway], 'offDiffs')
	defDiffAve = _percentStat(game[homeAway], 'defDiffs')
	data['offDiffAve'] = offDiffAve
	data['defDiffAve'] = defDiffAve
	data['scored'] = game['score'][homeAway]
	data['scoredAgainst'] = game['score'][other]
	data['mov'] = data['scored'] - data ['scoredAgainst']
	totShotsA = game[other]['2PtAttempted'] + game[other]['3PtAttempted']
	totMadeA =  game[other]['2PtMade'] + game[other]['3PtMade']
	data['totShotsAgainst'] = totShotsA
	data['totMadeAgainst'] = totMadeA
	data['turnoversGained'] = game[other]['turnovers']
	data['timesFouled'] = game[other]['fouls']
	statsAgainst = ['3PtAttempted', '3PtMade', 'FTAttempted','FTMade','turnovers','steals','offRebound','defRebound','posTime','blocks', 'possessions']
	for stat in statsAgainst:
		data['{}Against'.format(stat)] =  game[other][stat]
##	log.debug('data is {}'.format(data))
	print (data)
	return data

def insertStatData(game):
	homeStats = _setStatsData(game, 'home')
	awayStats = _setStatsData(game, 'away')
	h_ins = insertStats(homeStats)
	a_ins = insertStats(awayStats)

	return h_ins, a_ins

def reverseHomeAway(homeAway):
	if homeAway == 'home':
		return 'away'
	elif homeAway == 'away':
		return 'home'
	else:
		return None

def _percentStat(team, stat):
	ave = 0
	try:
		ave = sum(team[stat])/(1.0 * len(team[stat]))
	except:
		pass
	return ave

def insertStats(stats):
	c = dbConn.cursor()
	try:
		c.execute('''INSERT INTO stats(GameID, Team, Points, PointsAgainst, Mov, ShotsTaken, ShotsMade, ThreesTaken, ThreesMade, \
		FreesTaken, FreesMade, Turnovers, TurnoversForced, Steals, Blocks, OffReb, DefReb, FoulsCommitted,\
                TimesFouled, Top, Win, OffDiffAve, DefDiffAve, TotShotsAgainst, TotMadeAgainst, ThreesTakenAgainst,\
                ThreesMadeAgainst, FreesTakenAgainst, FreesMadeAgainst, StealsAgainst, BlocksAgainst, TopAgainst, Proccessed, possessionsFor, possessionsAgainst)
                Values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (stats['dataID'], stats['name'], stats['scored'], stats['scoredAgainst'],
				stats['mov'], stats['totShots'], stats['totMade'], stats['3PtAttempted'], stats['3PtMade'], stats['FTAttempted'], stats['FTMade'], stats['turnovers'],
				stats['turnoversGained'], stats['steals'], stats['blocks'], stats['offRebound'], stats['defRebound'], stats['fouls'], stats['timesFouled'],
				stats['posTime'], stats['win'], stats['offDiffAve'], stats['defDiffAve'], stats['totShotsAgainst'], stats['totMadeAgainst'], stats['3PtAttemptedAgainst'],
				stats['3PtMadeAgainst'], stats['FTAttemptedAgainst'], stats['FTMadeAgainst'], stats['stealsAgainst'], stats['blocksAgainst'], stats['posTimeAgainst'],0,
				stats['possessions'], stats['possessionsAgainst']) )
	except sqlite3.IntegrityError:
		return False
	dbConn.commit()
	if c.rowcount == 1:
		return True
	else:
		return False

def getWinner(game):
	if game['score']['home'] > game['score']['away']:
		return 'home'
	else:
		return 'away'

init()
insertStatData(stats)
