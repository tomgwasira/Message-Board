import sqlite3

connection = sqlite3.connect('data.db')
cursor = connection.cursor()

create_table = "CREATE TABLE people (id int, username text, password text)" # Schema
cursor.execute(create_table)

users = [(1, 'jose', 'asdf'), (2, 'rolf', 'xyz')]
insert_query = "INSERT INTO people VALUES(?, ?, ?)"

cursor.executemany(insert_query, users)

select_query = "SELECT * FROM people"
for row in cursor.execute(select_query):
	print(row)

connection.commit()

connection.close()