import inspect
import requests

from urllib.parse import urlencode
from services.logger import Logger

class Helper:

	def ParseRequestHeaders(request):

		try:
			return {k:v for k,v in request.headers.items()}

		except:
			return {}

	def ParseRequestBody(request):

		try:
			data = request.args if request.method == 'GET' else request.json

			return data if data else {}
			
		except:
			return {}

	def ParseRequestIp(request):

		try:
			return request.environ.get('HTTP_X_FORWARDED_FOR',request.remote_addr).split(',')[0].strip()

		except:
			return False
		
	def Forwarder(method,endpoint,payload):

		try:
			result = requests.post(endpoint,json = payload,stream = True) if method == 'POST' else requests.get(f'{endpoint}?{urlencode(payload)}',stream = True)

			return result.headers, result.json()

		except Exception as e:
			Logger.CreateExceptionLog(inspect.stack()[0][3],str(e),f'ERROR - Could not forward request: {endpoint}')

			return False, False