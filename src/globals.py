from enum import Enum

### Config ###
LOG_FOLDER_NAME = "logs"
SUBREDDIT = "testfakecbb"
CONFIG_SUBREDDIT = "testFakeCBB"
USER_AGENT = "FakeCBBRef (by /u/Watchful1 and /u/Zenverak)"
OWNER = "zenverak"
LOOP_TIME = 2*60
DATABASE_NAME = "database.db"
SUBREDDIT_LINK = "https://www.reddit.com/r/{}/comments/".format(SUBREDDIT)
ACCOUNT_NAME = "default"
timeouts = 4
delayHours = 24
ifoulTime = 3


statSheet = '13llhH_3hmYwmmuyF9X7gCEo-cAK9SIFDqEqSrIZ7tkk'
rangeSheetProd = '1xJOn_j64vTIispeuf59OD_8-i5AjYZFt36YKm1_XzmY'
rangeSheetDev = '1ud125PTc4dwuWfkTe3w-cbKvHPLbsOt7T5Q_DD-AFfE'
week = 'sheet1'

### Constants ###
offPlays = ['push', 'average','chew']
pointResults = ['made 2pt', 'made 3pt', 'made 3pt and foul', 'made 2pt and foul']
foulPlays = ['made 3pt and foul', 'made 2pt and foul','fouled on 2pt', 'fouled on 3pt']
foulMissPlays = ['fouled on 2pt', 'fouled on 3pt']
missPlays = ['missed 2pt', 'missed 3pt']
conversionPlays = ['freeThrow',]
nonShootingFoul = ['Foul', 'foul', 'ifoul','nonshooting foul']
offRebounds = ['offensive rebound']
turnovers = ['steal', 'turnover']
switchPossessions = ['turnover', 'made','freeDone','block','miss', 'steal']
stealDunk = 'stealdunk'
steal3Pt = 'steal3pt'
intFoul ='ifoul'

datatag = " [](#datatag"
singleBonus = 7
doubleBonus = 10
halfLength = 10*60
otLength =  4*60
maxRange = 1000

### Log ###
logGameId = ""
gameId = None
