import mysql.connector
import inspect
import settings

from services.logger import Logger

class Db:

	def Connect(write = False,raw = False):

		try:
			return mysql.connector.connect(
				host = settings.DB_HOST_WRITER if write else settings.DB_HOST_READER,
				port = settings.DB_PORT,
				user = settings.DB_USER,
				password = settings.DB_PASS,
				database = '' if raw else settings.DB_NAME
			)

		except:
			return False

	def Disconnect(con):

		try:
			return con.close()

		except:
			return False

	def ExecuteQuery(query,inputs = None,write = False,raw = False,rowid = False):

		con = Db.Connect(write,raw)

		if not con:
			return False

		try:
			result = False

			if str(query).strip().lower().startswith('select'):
				cursor = con.cursor(dictionary = True)
				cursor.execute(query,inputs)
				
				result = cursor.fetchall()

			else:
				cursor = con.cursor()

				if type(inputs) is list:
					cursor.executemany(query,inputs)

				else:
					cursor.execute(query,inputs)
				
				con.commit()

				result = cursor.lastrowid if rowid else True
			
			cursor.close()

			Db.Disconnect(con)

			return result

		except Exception as e:
			Db.Disconnect(con)
			Logger.CreateExceptionLog(inspect.stack()[0][3],str(e),query.strip())

			return False