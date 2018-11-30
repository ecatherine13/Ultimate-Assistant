import sqlite3
import os

db_fpath = os.path.join(os.path.curdir, "master.db") # current directory refers to directory open in command line, not that of this file
conn = None
cs = None

try:
	conn = sqlite3.connect(db_fpath)
	cs = conn.cursor()
	print("Connected to database\n")
except Error as e:
	print(e)

def close_connection():
	try:
		conn.commit()
		conn.close()
		print("\nDatabase connection closed\n")
	except Error as e:
		print(e)