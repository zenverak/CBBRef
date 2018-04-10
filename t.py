import sqlite3
from datetime import datetime
dbConn = sqlite3.connect('database.db')



def insertNewPlays(gameid, ocoach, dcoach, ptype, call, onum, dnum, diff, result):

	c = dbConn.cursor()
	try:
		c.execute('''insert into plays(GameID ,OffCoach ,DefCoach ,Playtype ,Call ,ONum ,Dnum ,Diff , Result)\
	values(?,?,?,?,?,?,?,?,?)''',(gameid ,ocoach ,dcoach ,ptype ,call ,onum ,dnum ,diff ,result))
		print ("should be inserted")

	except sqlite3.IntegrityError:
		return False
	dbConn.commit()
	return c.lastrowid



gid = 1
oc = 'h'
dc = '23'
ptype = "tes't"
call = 'dd'
onum = 9
dnum = 9
diff = 9
result = 'hdkf'




insertNewPlays(gid, oc, dc, ptype, call, onum, dnum, diff, result)
