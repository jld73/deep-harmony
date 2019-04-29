import re
import sys
print(sys.argv)

with open(sys.argv[1], 'r') as file:
	#print(file.readlines()[0])
	txt = file.read()
	
	if ':' in txt:
		r = re.compile('[-]')
		txt = re.sub(r, 'dash', txt)
		r = re.compile('[:]')
		txt = re.sub(r, 'sep', txt)
		r = re.compile('[>]')
		txt = re.sub(r, 'rab', txt)
		r = re.compile('[<]')
		txt = re.sub(r, 'lab', txt)
		r = re.compile('[#]')
		txt = re.sub(r, 'sharp', txt)
		r = re.compile('[/]')
		txt = re.sub(r, 'over', txt)
		#print(txt)
		with open("bach/nbach.csv", 'w') as out:
			print('writing to bach/nbach.csv')
			out.write(txt)
	else:
		r = re.compile('(dash)')
		txt = re.sub(r, '-', txt)
		r = re.compile('sep')
		txt = re.sub(r, ':', txt)
		r = re.compile('rab')
		txt = re.sub(r, '>', txt)
		r = re.compile('lab')
		txt = re.sub(r, '<', txt)
		r = re.compile('sharp')
		txt = re.sub(r, '#', txt)
		r = re.compile('over')
		txt = re.sub(r, '/', txt)
		r = re.compile(',')
		txt = re.sub(r, ' ', txt)
		r = re.compile('([abcdefg])([b#]?)-')
		txt = re.sub(r, lambda m : m.group(1).upper() + m.group(2) + "-", txt)
		#print(txt)
		with open("out.csv", 'w') as out:
			print('writing to out.csv')
			out.write(txt)
