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

### Constants ###
movementPlays = ['push', 'average','chew']
scorePlays = ['Made 2pt', 'Made 3pt']
foulScore = ['Made 3pt and Foul', 'Made 2pt and Foul']
conversionPlays = ['freeThrow',]
datatag = " [](#datatag"
halfLength = 10*60
maxRange = 1000

### Log ###
logGameId = ""
gameId = None
