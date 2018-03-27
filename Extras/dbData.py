import sqlite3
import globals

dbName = globals.DATABASE_NAME
print(dbName)
dbConn = sqlite3.connect('../'+globals.DATABASE_NAME)
c = dbConn.cursor()


def get_data(type_):
    execString ='''
        SELECT {}
        FROM games
        '''.format(type_)


    result = c.execute(execString)
    return result.fetchone()



h = get_data('homeTip')

