

##IF(ISNA(VLOOKUP(A3,week1!B1:ZY150, 2)),0, VLOOKUP(A3,week1!B1:ZY150, 2))

def create_formulas(weeks, num):
    start = ['=SUM(']
    for week in range(1,weeks):
        start.append("IF(ISNA(VLOOKUP($A2,week{0}!$B$1:$ZY$150, {1})),0, VLOOKUP($A2,week{0}!$B$1:$ZY$150, {1})),".format(week,num))
    start.append(')\n')
    return ''.join(start)





f = open('form.txt', 'w')
for i in range(2,32):
    f.write(create_formulas(23,i))
f.close()
        
        
