from flask import Flask
from flask import request
import redis

import proxy as Proxy
import configure as Configs

app = Flask("__name__")

@app.route('/')
def welcome():
	strr = '''
		<h3>Welcome to IP proxy pooling</h3><br>
		Access <strong>/myIP</strong> to retrieve 'remote address' header in GET request. For IP validation.<br>
		Access <strong>/getIP</strong> to retrieve an Proxy IP, format: IP:PORT<br>
		<p>Ethan Huang, <a href="https://journal.ethanshub.com/">https://journal.ethanshub.com/</a></p>
	'''
	return strr

@app.route("/myIP", methods=["GET"])
def myIP():
    return request.remote_addr

@app.route("/getIP")
def getIP():
    return Proxy.get_one_ip()

if __name__ == '__main__':
    app.run('0.0.0.0',5000)