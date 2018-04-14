from enum import Enum

### Config ###
LOG_FOLDER_NAME = "logs"
SUBREDDIT = "testFakeCBB"
CONFIG_SUBREDDIT = "testFakeCBB"
USER_AGENT = "FakeCBBRef (by /u/Watchful1 and /u/Zenverak)"
OWNER = "zenverak"
LOOP_TIME = 2*60
DATABASE_NAME = "database.db"
SUBREDDIT_LINK = "https://www.reddit.com/r/{}/comments/".format(SUBREDDIT)
ACCOUNT_NAME = "default"
timeouts = 4
delayHours = 24


statSheet = '13llhH_3hmYwmmuyF9X7gCEo-cAK9SIFDqEqSrIZ7tkk'

### Constants ###
offPlays = ['push', 'average','chew']
pointResults = ['made 2pt', 'made 3pt', 'made 3pt and foul', 'made 2pt and foul']
foulPlays = ['made 3pt and foul', 'made 2pt and foul','fouled on 2pt', 'fouled on 3pt']
foulMissPlays = ['fouled on 2pt', 'fouled on 3pt']
missPlays = ['missed 2pt', 'missed 3pt']
conversionPlays = ['freeThrow',]
nonShootingFoul = ['Foul', 'foul', 'ifoul']
offRebounds = ['offensive rebound']
turnovers = ['steal', 'turnover']
switchPossessions = ['turnover', 'made','freeDone','block','miss', 'steal']
intFoul ='ifoul'

datatag = " [](#datatag"
singleBonus = 7
doubleBonus = 10
halfLength = 20
otLength =  4*60
maxRange = 1000

### Log ###
logGameId = ""
gameId = None
