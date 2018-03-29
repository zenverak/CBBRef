import sqlite3




dbName = 'database.db'
dbConn = sqlite3.connect('../'+dbName)
c = dbConn.cursor()


def get_data(type_):
	execString ='''
		SELECT {}
		FROM games
		'''.format(type_)


	result = c.execute(execString)
	return result.fetchone()



def clearGameErroredOnly(gameID):
	execString = "update games set errored = 0 where ID = {}".format(gameID)
	
	try:
		c = dbConn.cursor()
		c.execute(execString)
		dbConn.commit()
	except Exception as err:
		return False
	return True

def saveDefensiveNumber(gameID, number):
	c = dbConn.cursor()
	c.execute('''
		UPDATE games
		SET Playclock = DATETIME(CURRENT_TIMESTAMP, '+24 hours')
			,DefenseNumber = ?
		WHERE ID = ?
	''', (number, gameID))
	dbConn.commit()



#print (True == clearGameErroredOnly(1))
saveDefensiveNumber(1,33)
