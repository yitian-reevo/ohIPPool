import time
import configure as Configs

def log(level, module_name, content):
	file = open(Configs.LOG_FILE, 'a', encoding='utf-8')
	#global file
	if Configs.LOG_TYPE == 0:
		fn = print
	elif Configs.LOG_TYPE == 1:
		fn = file.write
	else:
		fn = print

	strr = "[{0:d}][{1:s}] --- {2:12s} --- {3:s}".format(level, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), module_name, content)
	
	if level >= Configs.LOG_LEVEL:
		if fn == file.write:
			strr = strr + '\n'

		fn(strr)

	file.close()

