# Coded with ingenuity,
# by Jawwad Abbasi (jawwad@omnitryx.ca)

# Initiates a Flask app to handle managed endpoints
# and relays to corresponding controller and module
# for processing.

import json
import sentry_sdk
import settings

from flask import Flask,Response,request
from v1.api import Api
from v1.cache import Cache

sentry_sdk.init(
	dsn = settings.SENTRY_DSN,
	traces_sample_rate = settings.SENTRY_TRACES_SAMPLE_RATE,
	profiles_sample_rate = settings.SENTRY_PROFILES_SAMPLE_RATE,
	environment = settings.SENTRY_ENVIRONMENT
)

Cache.Connect()

app = Flask(__name__)

@app.errorhandler(404)
def RouteNotFound(e):

	return Response(None,status = 400,mimetype = 'application/json')

####################################
# Supported endpoints for API v1
####################################
@app.route('/<path:path>',methods = ['GET','POST'])
def Handler(path):

	data = Api.Handler(request)
	return Response(json.dumps(data),status = data['ApiHttpResponse'],mimetype = 'application/json')

####################################
# Initiate web server
####################################
app.run(host = '0.0.0.0',port = settings.FLASK_PORT,debug = settings.FLASK_DEBUG)