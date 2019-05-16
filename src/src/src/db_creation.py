import sqlite3

connection = sqlite3.connect('message_board.db')
cursor = connection.cursor()

# users Table
create_table = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username text, password text, firstname text, lastname text)" # users table schema
cursor.execute(create_table)

# messages Table
create_table = "CREATE TABLE IF NOT EXISTS messages (name text, message_content text, likes int, dislikes int, group_ text, creator text, date_created text)" # messages table schema
cursor.execute(create_table)

# groups Table
create_table = "CREATE TABLE IF NOT EXISTS groups (groupname text, username text)" # groups table schema
cursor.execute(create_table)


cursor.execute("INSERT INTO groups VALUES ('Errors', 'permanent')")
cursor.execute("INSERT INTO groups VALUES ('Purchases', 'permanent')")
cursor.execute("INSERT INTO groups VALUES ('Complaints', 'permanent')")
cursor.execute("INSERT INTO groups VALUES ('Codes', 'permanent')")
#cursor.execute("INSERT INTO messages VALUES ('Tom is great.', 'Hi guys. Im struggling to figure out the code for the meter.', 0, 'Errors', 'thomas', '14/05/2019')")

connection.commit()
connection.close()