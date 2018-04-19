import sheets



def setS():
	#Team	shots taken	shot made	shooting percentage	3pt taken	3pt made
	#3 shooting per	ftTaken	ftMade	ftPer	turnovers	steals	oreb	def reb
	#fouls commited	,times fouled	,time of possession

	stats = ['Akron', 1, 1, 100.0, 1, 1, 100.0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,20, 1]
	sheets.setStats(stats)


setS()
