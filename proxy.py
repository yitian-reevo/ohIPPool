from multiprocessing import Process, Lock
from random import choice
import redis
import time
import requests
import ast
import sys

import webapi
import configure as Configs
import logger as Logger

redis_client = redis.StrictRedis(host=Configs.REDIS_HOST, port=Configs.REDIS_PORT, db=0)

def fn_retriever():
	global redis_clent
	fn_name = sys._getframe().f_code.co_name
	while True:
		Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "Routine Retriever Start.")
		cnt = redis_client.zcard(Configs.REDIS_KEY)
		ip_cnt_needed = Configs.POOL_SIZE - redis_client.zcard(Configs.REDIS_KEY)

		if ip_cnt_needed <= 0:
			Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "Enough IP(s) in Redis.")
			Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "Entering Sleep: {0:d}s.".format(Configs.RETRIEVER_INTERVAL))
			time.sleep(Configs.RETRIEVER_INTERVAL)
			continue

		tid = Configs.DAXIANG_RPOXY_ORDERID
		url = "http://tvp.daxiangdaili.com/ip/?tid={0:s}&num={1:d}&delay=5&category=2&sortby=time&filter=on&format=json&protocol=https".format(tid, ip_cnt_needed)

		try:
			response = requests.get(url)
			content = None

			if response.status_code == requests.codes.ok:
				content = response.text
		except Exception as e:
			print (e)

		res_json = ast.literal_eval(content.strip())

		if res_json:
			for addr in res_json:
				if addr.get('error'):
					continue
				redis_client.zadd(Configs.REDIS_KEY, Configs.MEDIUM, '{0:s}:{1:d}'.format(addr.get('host'), addr.get('port')))

		Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "Refill {0:d} IP(s) to Redis.".format(ip_cnt_needed))

def __validation(addr):
	proxies = {
		"http": "http://{0}".format(addr),
		"https": "http://{0}".format(addr)
	}

	header = {}
	header['user-agent'] = choice(Configs.FakeUserAgents)

	try:
		response = requests.get("http://52.206.77.228:5000/myIP", headers=header, proxies=proxies, timeout=5)
	except Exception as e:
		return False
	else:
		if response.status_code == requests.codes.ok:
			#print (response.text)
			return True

def fn_validator():
	global redis_clent
	fn_name = sys._getframe().f_code.co_name
	while True:
		# Test all ips whose score >= POOL_IP_QUALITY - 1
		# False ==> score - 1
		# True  ==> score + 1 
		maxscore = redis_client.zrange(Configs.REDIS_KEY, 0, 0, desc=True, withscores=True)
		if not maxscore:
			Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "Pool is empty. Entering Sleep: {0:d}s.".format(Configs.VALIDATOR_INTERVAL))
			time.sleep(Configs.VALIDATOR_INTERVAL)
			continue

		maxscore = maxscore[0][1]
		Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "Max score in this round: {0:d}.".format(int(maxscore)))
		res = redis_client.zrangebyscore(Configs.REDIS_KEY, Configs.POOL_IP_QUALITY - 1, maxscore)
		Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "Start to Validate {0:d} IP(s).".format(len(res)))

		increment = []

		i = 0
		for ip in res:
			n = 1 if __validation(ip.decode('utf-8')) else -1
			increment.append([ip, n])
			Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "[{0:d}]Validated[{1:s}], Result:[{2:d}].".format(i, ip.decode('utf-8'), n))
			i += 1
			
		for inc in increment:
			redis_client.zincrby(Configs.REDIS_KEY, inc[0], inc[1])

		Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "Validation finished. Entering Sleep: {0:d}s.".format(Configs.VALIDATOR_INTERVAL))
		time.sleep(Configs.VALIDATOR_INTERVAL)
		

def fn_cleaner():
	global redis_clent
	fn_name = sys._getframe().f_code.co_name
	while True:
		# Remove all ips whose score < POOL_IP_QUALITY
		res = redis_client.zremrangebyscore(Configs.REDIS_KEY, -1, Configs.POOL_IP_QUALITY - 1)
		Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "Remove {0:d} IP(s) from Redis.".format(res))
		Logger.log(Configs.LOG_LEVEL_FINE, fn_name, "Entering Sleep: {0:d}s.".format(Configs.CLEANER_INTERVAL))
		time.sleep(Configs.CLEANER_INTERVAL)
	

def fn_webapi():
	webapi.app.run(host=Configs.API_ADDR, port=Configs.API_PORT)

def get_one_ip():
	global redis_clent
	cnt = redis_client.zrange(Configs.REDIS_KEY, 0, 0, desc=True)
	redis_client.zincrby(Configs.REDIS_KEY, cnt[0], -1)
	
	if cnt:
		return cnt[0].decode('utf-8')
	else:
		return 'ERROR|TRY AGAIN LATER'

def main():
	process_webapi = Process(target=fn_webapi)
	process_webapi.start()
	time.sleep(5)
	
	process_retriever = Process(target=fn_retriever)
	process_retriever.start()

	
	process_validator = Process(target=fn_validator)
	process_validator.start()

	process_cleaner = Process(target=fn_cleaner)
	process_cleaner.start()

	
 
if __name__ == '__main__':
	main()
	#r = redis.StrictRedis(host=Configs.REDIS_HOST, port=Configs.REDIS_PORT, db=0)
	#print (r.zincrby(Configs.REDIS_KEY, '123.23.3.3', -10))
	#print (r.zadd(Configs.REDIS_KEY, 5, '123.23.3.3'))
	#print (r.zadd(Configs.REDIS_KEY, 5, '123.23.3.3'))
	#print (r.zadd(Configs.REDIS_KEY, 5, '123.23.3.3'))
	#print (r.zadd(Configs.REDIS_KEY, 5, '123.23.3.3'))
	#ret = r.sscan(1)
	#print (ret)