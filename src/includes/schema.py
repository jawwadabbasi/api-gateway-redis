import settings

from includes.db import Db

class Schema:

	def CreateDatabase():

		query = f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME} CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci"

		return Db.ExecuteQuery(query, None, True, True)

	def CreateTables():

		#####################################################################################################
		query = """
			CREATE TABLE IF NOT EXISTS requests (
				request_id VARCHAR(255) PRIMARY KEY NOT NULL,
				method VARCHAR(255) NOT NULL,
				endpoint VARCHAR(255) NOT NULL,
				request JSON DEFAULT NULL,
				response JSON DEFAULT NULL,
				meta JSON DEFAULT NULL,
				ip_address VARCHAR(255) NOT NULL,
				date DATETIME NOT NULL
			) ENGINE=INNODB;
		"""

		if not Db.ExecuteQuery(query,None,True):
			return False

		Db.ExecuteQuery("ALTER TABLE requests ADD INDEX method (method);",None,True)
		Db.ExecuteQuery("ALTER TABLE requests ADD INDEX endpoint (endpoint);",None,True)
		Db.ExecuteQuery("ALTER TABLE requests ADD INDEX ip_address (ip_address);",None,True)
		Db.ExecuteQuery("ALTER TABLE requests ADD INDEX date (date);",None,True)
		#####################################################################################################

		return True