team = {'tag': 'akron',
        'name': 'Akron',
        'offense': 'spread',
        'defense': '3-4',
        'coaches': ['zenverak'],
        'yardsPassing': 0,
        'yardsRushing': 0,
        'yardsTotal': 0,
        'turnoverInterceptions': 0,
        'turnoverFumble': 0,
        'fieldGoalsScored': 0,
        'fieldGoalsAttempted': 0,
        'posTime': 0,
        'record': None,
        'playclockPenalties': 0}


def flair(team):
	print (team)
	return "[{}](#f/{})".format(team['name'], team['tag'])


print (flair(team))
