import re


range_ =  {'500-490': {'result': 'Turnover'}, '489-477': {'result': 'Steal'}, '476-466': {'result': 'Block'}, '465-362': {'result': 'Missed 3pt'}, '361-232': {'result': 'Missed 2pt'}, '231-208': {'result': 'Fouled on 2 Pt'}, '209-190': {'result': 'Offensive rebound'}, '189-114': {'result': 'Made 2pt', 'points': 2}, '113-95': {'result': 'Fouled on 3pt'}, '94-85': {'result': 'Made 2pt and Foul', 'points': 2}, '84-11': {'result': 'Made 3pt', 'points': 3}, '10-0': {'result': 'Made 3pt and Foul', 'points': 3}}


def findNumberInRangeDict(number, dict):
#	log.debug('Finding where this number, {} ,lies in the dictionary: {}'.format(number, dict))
	for key in dict:
		rangeEnd, rangeStart = getRange(key)
		print('rangeStart is {} and rangeEnd is {}'.format(rangeStart, rangeEnd))
		if rangeStart is None:
#			log.warning("Could not extract range: {}".format(key))
			continue

		if rangeStart <= number <= rangeEnd:
#			log.debug('found the dict[key] and it is {}'.format(dict[key]))
			return dict[key]

#	log.warning("Could not find number in dict")
	return None

def getRange(rangeString):
	rangeEnds = re.findall('(\d+)', rangeString)
	if len(rangeEnds) < 2 or len(rangeEnds) > 2:
		return None, None
	return int(rangeEnds[0]), int(rangeEnds[1])





num = 489

print (findNumberInRangeDict(num, range_))



