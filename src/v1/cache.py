import inspect
import json
import redis
import settings

from services.logger import Logger

class Cache:

	def Connect():

		try:
			settings.REDIS_CLIENT = redis.Redis(
				host = settings.REDIS_HOST,
				port = settings.REDIS_PORT,
				db = settings.REDIS_DB,
				ssl = settings.REDIS_SSL,
				decode_responses = True
			)

		except Exception as e:
			Logger.CreateExceptionLog(inspect.stack()[0][3],str(e),'ERROR - Could not connect with cache')

			return False
		
	def Clear():

		try:
			settings.REDIS_CLIENT.flushdb()

		except Exception as e:
			Logger.CreateExceptionLog(inspect.stack()[0][3],str(e),'ERROR - Could not clear cache')

			return False
		
	def PrefixKey(key):

		return f'{settings.REDIS_KEY_PREFIX}:{key}'
	
	def PrefixKeyList(keys):

		data = []

		for x in keys:
			data.append(Cache.PrefixKey(x))

		return data
		
	def Set(key,value,expiration = None):

		try:
			kwargs = {
				'name': Cache.PrefixKey(key),
				'value': json.dumps(value)
			}

			if expiration:
				kwargs['ex'] = int(expiration)

			return settings.REDIS_CLIENT.set(**kwargs)

		except Exception as e:
			Logger.CreateExceptionLog(inspect.stack()[0][3],str(e),f'ERROR - Could not set cache: {key}')

			return False
		
	def Get(key):

		try:
			data = settings.REDIS_CLIENT.get(Cache.PrefixKey(key))
			
			return json.loads(data) if data else None

		except Exception as e:
			Logger.CreateExceptionLog(inspect.stack()[0][3],str(e),f'ERROR - Could not retrieve cache: {key}')

			return None
		
	def Delete(keys):

		try:
			for x in keys:
				if type(x) == str and '*' in x:
					data = list(settings.REDIS_CLIENT.scan_iter(match = Cache.PrefixKey(x)))
					data and settings.REDIS_CLIENT.delete(*data)

				elif type(x) == list:
					settings.REDIS_CLIENT.delete(*Cache.PrefixKeyList(x))
				
				else:
					settings.REDIS_CLIENT.delete(Cache.PrefixKey(x))

			return True

		except Exception as e:
			Logger.CreateExceptionLog(inspect.stack()[0][3],str(e),f'ERROR - Could not delete from cache: {json.dumps(keys)}')

			return False