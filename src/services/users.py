import requests
import settings

from urllib.parse import urlencode

class Users:

	api_endpoint = settings.DNS_BATMAN_USERS

	def VerifySession(cookie):

		data = {
			'Cookie': cookie
		}

		data = urlencode(data)

		try:
			result = requests.get(f'{Users.api_endpoint}/api/v1/User/VerifySession?{data}',stream = True)

			return result.json()['ApiResult'] if result.ok else False

		except:
			return False