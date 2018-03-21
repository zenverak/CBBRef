from enum import Enum

### Config ###
LOG_FOLDER_NAME = "logs"
SUBREDDIT = "FakeCBB"
CONFIG_SUBREDDIT = "FakeCBB"
USER_AGENT = "FakeCBBRef (by /u/Watchful1 and /u/Zenverak)"
OWNER = "zenverak"
LOOP_TIME = 2*60
DATABASE_NAME = "database.db"
SUBREDDIT_LINK = "https://www.reddit.com/r/{}/comments/".format(SUBREDDIT)
ACCOUNT_NAME = "default"

### Constants ###
movementPlays = ['run', 'pass']
normalPlays = ['run', 'pass', 'punt', 'punt', 'fieldGoal']
timePlays = ['kneel', 'spike']
conversionPlays = ['pat', 'twoPoint']
datatag = " [](#datatag"
quarterLength = 10*60

### Log ###
logGameId = ""
gameId = None
