import json
import uuid
import concurrent.futures
import settings

from includes.db import Db
from v1.helper import Helper
from v1.library import Library
from v1.cache import Cache

class Api:

	def Track(method,endpoint,request,response,meta,ip_address):

		query = """
			INSERT INTO requests
			SET request_id = %s,
				method = %s,
				endpoint = %s,
				request = %s,
				response = %s,
				meta = %s,
				ip_address = %s,
				date = NOW()
		"""

		inputs = (
			str(uuid.uuid4()),
			method,
			endpoint,
			json.dumps(request),
			json.dumps(response),
			json.dumps(meta),
			ip_address
		)

		return Db.ExecuteQuery(query,inputs,True)

	def Response(request,response,lib_data,cache_data,fw_data):
		
		if lib_data and not lib_data['requires_tracking']:
			return response
		
		executor = concurrent.futures.ThreadPoolExecutor()
		executor.submit(
			Api.Track,
			request.method,
			request.path,
			{
				'Headers': Helper.ParseRequestHeaders(request),
				'Body': Helper.ParseRequestBody(request)
			},
			response,
			{
				'Library': lib_data,
				'Cache': cache_data,
				'Forwarder': fw_data
			},
			Helper.ParseRequestIp(request)
		)

		return response

	def Handler(request):

		api_data = {}
		api_data['ApiHttpResponse'] = 500
		api_data['ApiMessages'] = []
		api_data['ApiResult'] = []

		request_headers = Helper.ParseRequestHeaders(request)
		request_ip = Helper.ParseRequestIp(request)
		request_body = Helper.ParseRequestBody(request)
		
		cookie = request_headers.get(settings.AUTH_HEADER_NAME)
		session_data = Library.GetSessionData(cookie) if cookie else {}
		
		request_body = Library.MergeSessionData(
			request_ip,
			request_body,
			cookie,
			session_data
		)

		if request_body is False:
			api_data['ApiHttpResponse'] = 500
			api_data['ApiMessages'] += ['ERROR - Could not parse request body']

			return Api.Response(request,api_data,None,None,None)
		
		lib_data = Library.Exceptions(
			request.method,
			request.path,
			request.full_path,
			request_body,
			cookie,
			session_data
		)

		if lib_data:
			return lib_data

		lib_data = Library.Standard(
			request.method,
			request.path,
			request.full_path,
			request_body,
			cookie,
			session_data
		)

		if not lib_data:
			api_data['ApiHttpResponse'] = 404
			api_data['ApiMessages'] += ['INFO - The requested resource was not found']

			return Api.Response(request,api_data,lib_data,None,None)
		
		if lib_data['requires_auth'] and not session_data:
			api_data['ApiHttpResponse'] = 403
			api_data['ApiMessages'] += ['INFO - Unauthorized']

			return Api.Response(request,api_data,lib_data,None,None)
		
		cache_data = Cache.Get(lib_data['cache_key']) if lib_data['requires_caching'] else None

		if cache_data:
			return Api.Response(request,cache_data,lib_data,cache_data,None)
		
		fw_x, fw_data = Helper.Forwarder(request.method,lib_data['endpoint'],request_body)

		if not fw_x:
			api_data['ApiHttpResponse'] = 500
			api_data['ApiMessages'] += ['ERROR - Unexpected error occurred']

			return Api.Response(request,api_data,lib_data,cache_data,fw_data)
		
		if (request.method == 'GET'
	  		and lib_data['requires_caching']
			and not cache_data
			and int(fw_data['ApiHttpResponse']) in [200,201,202]
		):
			executor = concurrent.futures.ThreadPoolExecutor()
			executor.submit(
				Cache.Set,
				lib_data['cache_key'],
				fw_data,
				lib_data['cache_ttl']
			)

		if (request.method == 'POST'
	  		and lib_data['cache_delete']
			and int(fw_data['ApiHttpResponse']) in [200,201,202]
		):
			Cache.Delete(lib_data['cache_delete'])

		return Api.Response(request,fw_data,lib_data,cache_data,fw_data)