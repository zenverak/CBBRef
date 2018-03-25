
F = 'plays.txt'
F = 'teams.txt'
pre = 'fix_'
f = open(F, 'r')

line = f.readlines()[0]
start = 0
new_f = open(pre+F,'w')
while True:
    point = line.find(' ', start)
    if point == -1:
        break
    new_f.write(line[start:point]+'\n')
    start = point+1

f.close()
new_f.close()
    
