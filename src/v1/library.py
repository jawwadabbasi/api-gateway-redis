import concurrent.futures
import inspect
import settings
from services.logger import Logger
from services.users import Users
from v1.cache import Cache

class Library:

	def GetSessionData(cookie):

		data = Cache.Get(f'cookie:{cookie}')

		if data:
			return data
		
		data = Users.VerifySession(cookie)

		if not data or not data.get('UserId'):
			return {}
		
		executor = concurrent.futures.ThreadPoolExecutor()
		executor.submit(Cache.Set,f'cookie:{cookie}',data,settings.DNS_BATMAN_USERS)

		return data
	
	def MergeSessionData(request_ip,request_body,cookie,session_data):

		try:
			data = {
				'IpAddress': request_ip,
				**({'Cookie': cookie} if cookie else {}),
				**({'UserId': session_data['UserId']} if session_data and 'UserId' in session_data else {}),
			}

			return request_body | data
		
		except Exception as e:
			Logger.CreateExceptionLog(inspect.stack()[0][3],str(e),f'ERROR - Could not merge session data: {cookie}')

			return False
		
	def ExcAppVersion(request_body):

		api_data = {}
		api_data['ApiHttpResponse'] = 500
		api_data['ApiMessages'] = []
		api_data['ApiResult'] = []

		if (not request_body.get('Platform')
	  		or not request_body.get('Version')
		):
			api_data['ApiHttpResponse'] = 400
			api_data['ApiMessages'] = ['ERROR - Missing required parameters']

			return api_data
		
		try:
			platform = str(request_body.get('Platform')).strip().lower()
			version = str(request_body.get('Version')).strip()

		except:
			api_data['ApiHttpResponse'] = 400
			api_data['ApiMessages'] = ['ERROR - Invalid arguments']

			return api_data
		
		api_data['ApiResult'] = 'latest' if version in ['1.0.19','1.0.20','1.0.21'] else 'deprecated'

		api_data['ApiHttpResponse'] = 200
		api_data['ApiMessages'] += ['INFO - Request processed successfully']

		return api_data
		
	def ExcVerifySession(session_data):

		api_data = {}
		api_data['ApiHttpResponse'] = 500
		api_data['ApiMessages'] = []
		api_data['ApiResult'] = []

		if not session_data:
			api_data['ApiHttpResponse'] = 403
			api_data['ApiMessages'] += ['INFO - Unauthorized']

			return api_data
		
		api_data['ApiHttpResponse'] = 202
		api_data['ApiMessages'] += ['INFO - Request processed successfully']

		api_data['ApiResult'] = session_data

		return api_data
		
	def Exceptions(request_method,request_path,request_full_path,request_body,cookie,session_data):

		if request_method == 'GET' and request_path == '/App/Version':
			return Library.ExcAppVersion(request_body)

		if request_method == 'GET' and request_path == '/User/VerifySession':
			return Library.ExcVerifySession(session_data)

		return False
		
	def Standard(request_method,request_path,request_full_path,request_body,cookie,session_data):

		user_id = session_data.get('UserId')
		profile_id = request_body.get('ProfileId')

		data = {
			'/Log/Exception': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Exception/CreateLog',
				'requires_auth': False,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': []
			},
			'/App/Meta': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/App/Meta',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': []
			},
			'/App/Plans': {
				'method': 'GET',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/App/Plans',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': 300,
				'cache_key': f'user_id:{{{user_id}}}:pricing_plans',
				'cache_delete': []
			},
			'/User/Login': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/User/Login',
				'requires_auth': False,
				'requires_tracking': True,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': []
			},
			'/User/Logout': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/User/Logout',
				'requires_auth': True,
				'requires_tracking': True,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					f'cookie:{cookie}',
					f'user_id:{{{user_id}}}:*'
				]
			},
			'/User/Get': {
				'method': 'GET',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/User/Get',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': True,
				'cache_ttl': 1800,
				'cache_key': f'user_id:{{{user_id}}}:data',
				'cache_delete': []
			},
			'/User/Delete': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/User/Delete',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					f'cookie:{cookie}',
					f'user_id:{{{user_id}}}:*'
				]
			},
			'/User/Onboard': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/User/Onboard',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					f'user_id:{{{user_id}}}:data'
				]
			},
			'/Profile/Create': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Profile/Create',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					f'cookie:{cookie}',
					f'user_id:{{{user_id}}}:*'
				]
			},
			'/Profile/Update': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Profile/Update',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					[
						f'user_id:{{{user_id}}}:profiles',
						f'user_id:{{{user_id}}}:profile_id:{profile_id}:data',
						f'user_id:{{{user_id}}}:profile_id:{profile_id}:notifications'
					]
				]
			},
			'/Profile/RemoveImage': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Profile/RemoveImage',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					[
						f'user_id:{{{user_id}}}:profiles',
						f'user_id:{{{user_id}}}:profile_id:{profile_id}:data',
						f'user_id:{{{user_id}}}:profile_id:{profile_id}:notifications'
					]
				]
			},
			'/Profile/Select': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Profile/Select',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					f'cookie:{cookie}',
					f'user_id:{{{user_id}}}:*'
				]
			},
			'/Profile/Get': {
				'method': 'GET',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Profile/Get',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': True,
				'cache_ttl': 1800,
				'cache_key': f'user_id:{{{user_id}}}:profile_id:{profile_id}:data',
				'cache_delete': []
			},
			'/Profile/UpdateSearchFilters': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Profile/UpdateSearchFilters',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					f'user_id:{{{user_id}}}:profile_id:{profile_id}:search_filters'
				]
			},
			'/Profile/GetSearchFilters': {
				'method': 'GET',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Profile/GetSearchFilters',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': True,
				'cache_ttl': 1800,
				'cache_key': f'user_id:{{{user_id}}}:profile_id:{profile_id}:search_filters',
				'cache_delete': []
			},
			'/Profile/Hide': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Profile/Hide',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					[
						f'user_id:{{{user_id}}}:profiles',
						f'user_id:{{{user_id}}}:profile_id:{profile_id}:data',
						f'user_id:{{{user_id}}}:profile_id:{profile_id}:notifications',
					]
				]
			},
			'/Profile/Notifications': {
				'method': 'GET',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Profile/Notifications',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': True,
				'cache_ttl': 300,
				'cache_key': f'user_id:{{{user_id}}}:profile_id:{profile_id}:notifications',
				'cache_delete': []
			},
			'/Purchase/Apple': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Purchase/Apple',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					f'user_id:{{{user_id}}}:*'
				]
			},
			'/Purchase/Google': {
				'method': 'POST',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Purchase/Google',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': None,
				'cache_delete': [
					f'user_id:{{{user_id}}}:*'
				]
			},
			'/Subscription/Get': {
				'method': 'GET',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Subscription/Get',
				'requires_auth': True,
				'requires_tracking': False,
				'requires_caching': True,
				'cache_ttl': 1800,
				'cache_key': f'user_id:{{{user_id}}}:subscription',
				'cache_delete': []
			},
			'/Ip/Details': {
				'method': 'GET',
				'endpoint': f'{settings.DNS_BATMAN_USERS}/api/v1/Ip/Details',
				'requires_auth': False,
				'requires_tracking': False,
				'requires_caching': False,
				'cache_ttl': None,
				'cache_key': request_full_path,
				'cache_delete': []
			},
		}

		x = data.get(request_path)

		return x if x and x['method'] == request_method else False