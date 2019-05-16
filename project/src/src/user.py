import sqlite3  # Gives class ability to interact with SQLite 3
from flask import Flask, request
from flask_restful import Resource

class User:
	def __init__(self, _id, username, password, firstname, lastname):
		self.id = _id
		self.username = username
		self.password = password
		self.firstname = firstname
		self.lastname = lastname

	
	# Creating mappings
	@classmethod
	def find_by_username(cls, username):
		connection = sqlite3.connect('message_board.db') # Set up connection
		cursor = connection.cursor()

		query = "SELECT * FROM users WHERE username=?"
		result = cursor.execute(query, (username,))   # Single value tuple

		row=result.fetchone()
		if row:
			user = cls(*row)   # Assigning the tuple from the database to variable user
		else:
			user = None

		connection.close()
		return user


	@classmethod
	def find_by_id(cls, _id):
		connection = sqlite3.connect('message_board.db') # Set up connection
		cursor = connection.cursor()

		query = "SELECT * FROM users WHERE id=?"
		result = cursor.execute(query, (_id,))   # Single value tuple

		row=result.fetchone()
		if row:
			user = cls(*row)   # Assigning the tuple from the database to variable user
		else:
			user = None

		connection.close()
		return user


class UserRegister(Resource):   # A resource to allow registration of users using API
	def post(self):
		data = request.get_json()

		if User.find_by_username(data['username']):
			return {"message": "A user with that username already exists"}

		connection = sqlite3.connect('message_board.db')
		cursor = connection.cursor()

		query = "INSERT INTO users VALUES (NULL, ?, ?, ?, ?)"
		cursor.execute(query, (data['username'], data['password'], data['firstname'], data['lastname']))
		# cursor.execute(query, ("hup", "yeah", "soclear", "theman"))

		connection.commit()
		connection.close()

		return {"message": "Registration complete"}, 201