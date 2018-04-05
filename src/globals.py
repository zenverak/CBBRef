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


### Constants ###
offPlays = ['push', 'average','chew']
pointResults = ['Made 2pt', 'Made 3pt', 'Made 3pt and Foul', 'Made 2pt and Foul']
foulPlays = ['Made 3pt and Foul', 'Made 2pt and Foul','Fouled on 2 Pt', 'Fouled on 3Pt']
foulMissPlays = ['Fouled on 2 Pt', 'Fouled on 3Pt']
missPlays = ['Missed 2pt', 'Missed 3pt']
conversionPlays = ['freeThrow',]
nonShootingFoul = ['Foul', 'foul']
offRebounds = ['Offensive rebound']
turnovers = ['Steal', 'Turnover']
switchPossessions = ['turnover', 'made','freeDone','block','miss']

datatag = " [](#datatag"
singleBonus = 7
doubleBonus = 10
halfLength = 10*60
otLength =  4*60
maxRange = 1000

### Log ###
logGameId = ""
gameId = None
