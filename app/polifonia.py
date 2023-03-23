from flask import Flask, render_template, request, url_for, redirect, session, Response
from urllib.parse import parse_qs , quote
import re
import requests

app = Flask(__name__)
MYENDPOINT = 'http://localhost:9999/bigdata/sparql'

@app.route("/")
def home():
	return render_template('index.html')

@app.route("/sparql", methods=['GET', 'POST'])
def sparql_gui(active=None):
	""" SPARQL endpoint GUI and request handler

	Parameters
	----------
	active: str
		Query string or None
		If None, renders the GUI, else parse the query (__run_query_string)
		If the query string includes an update, return error, else sends
		the query to the endpoint (__contact_tp)
	"""
	if request.method == 'GET':
		content_type = request.content_type
		q = request.args.get("query")
		return __run_query_string(active, q, content_type)
	else:

		content_type = request.content_type
		cur_data = request.get_data()
		if "application/x-www-form-urlencoded" in content_type:
			return __run_query_string(active, cur_data, True, content_type)
		elif "application/sparql-query" in content_type:
			return __contact_tp(cur_data, True, content_type)
		else:
			return render_template('sparql.html',active=active)

def __run_query_string(active, query_string,
	is_post=False, content_type="application/x-www-form-urlencoded"):
	try:
		query_str_decoded = query_string.decode('utf-8')
	except Exception as e:
		query_str_decoded = query_string
	parsed_query = parse_qs(query_str_decoded)

	if query_str_decoded is None or query_str_decoded.strip() == "":
		return render_template('sparql.html',active=active)

	if re.search("updates?", query_str_decoded, re.IGNORECASE) is None:
		if "query" in parsed_query or "select" in query_str_decoded.lower():
			return __contact_tp(query_string, is_post, content_type)
		else:
			return render_template('sparql.html',active=active)
	else:
		return render_template('403.html'), 403

def __contact_tp(data, is_post, content_type):
	accept = request.args.get('HTTP_ACCEPT')
	if accept is None or accept == "*/*" or accept == "":
		accept = "application/sparql-results+json"

	data = data if isinstance(data,bytes) else quote(data)
	if is_post:
		req = requests.post(MYENDPOINT, data=data,
							headers={'content-type': content_type, "accept": accept})
	else:
		req = requests.get("%s?query=%s" % (MYENDPOINT,data ),
						   headers={'content-type': content_type, "accept": accept})

	if req.status_code == 200:
		response = Response()
		response.headers['Access-Control-Allow-Origin'] = '*'
		response.headers['Access-Control-Allow-Credentials'] = 'true'
		response.headers['Content-Type'] = req.headers["content-type"]
		response.mimetype = "application/sparql-results+json"
		return req.json()
	else:
		return render_template('error.html',
			status_code=str(req.status_code),
			headers={"Content-Type": request.content_type},
			text=req.text)

@app.route('/error')
def error(status_code, headers, text):
	return render_template('error.html',status_code, headers, text)

@app.errorhandler(403)
def page_not_found(e):
	# note that we set the 403 status explicitly
	return render_template('403.html'), 403

if __name__ == "__main__":
	app.run()

