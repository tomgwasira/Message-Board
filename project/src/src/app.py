import time
import datetime
import sqlite3
from flask import Flask, render_template, flash, request, redirect, url_for, session, logging
from flask_restful import Api
from datetime import datetime, timedelta
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

from security import authenticate, identity
from user import UserRegister
# from message import Message, Messages
from groups import Groups
from messages import Messages

app = Flask(__name__)
app.secret_key = 'complicated'
api = Api(app)

now = datetime.now()
date_time = now.strftime("%d.%m.%Y %H:%M")

user_liked = ""
user_disliked = ""

@app.route('/')
def index():
	return redirect(url_for('login'))


# Register Form Class
class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    # email = StringField('Email', [validators.Length(min=6, max=50)])
    firstname = StringField('First name', [validators.Length(min=1, max=50)])
    lastname = StringField('Last name', [validators.Length(min=1, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User Registeration
@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		username = form.username.data
		firstname = form.firstname.data
		lastname = form.lastname.data
		password = sha256_crypt.encrypt(str(form.password.data))

		connection = sqlite3.connect('message_board.db')
		cursor = connection.cursor()

		query = "INSERT INTO users VALUES (NULL, ?, ?, ?, ?)"
		cursor.execute(query, (username, password, firstname, lastname))

		connection.commit()
		connection.close()

		flash('You are now registered.', 'success')

		session['logged_in'] = True
		session['username'] = username

		return redirect(url_for('messages'))

	return render_template('register.html', form=form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password_candidate = request.form['password']

		connection = sqlite3.connect('message_board.db')
		cursor = connection.cursor()

		# Get user by username
		query = "SELECT * FROM users WHERE username=?"
		result = cursor.execute(query, (username,))   # Single value tuple

		row=result.fetchone()
		if row:
			password = row[2]
			if sha256_crypt.verify(password_candidate, password):
				session['logged_in'] = True
				session['username'] = username
				flash('You are now logged in', 'success')
				return redirect(url_for('messages'))

			else:
				error = 'Invalid login'
				return render_template('login.html', error=error)
			
		else:
			error = 'Username not found'
			return render_template('login.html', error=error)

		connection.close()

	return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please login', 'danger')
			return redirect(url_for('login'))
	return wrap


# Logout
@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))


# Retrieving messages for a particular user
@app.route('/messages')
@is_logged_in
def messages():
	current_user = session['username']

	connection = sqlite3.connect('message_board.db')
	cursor = connection.cursor()

	# Obtaining the groups that the current user belongs to.
	query = "SELECT groupname FROM groups"
	result = cursor.execute(query)
	all_groups = []

	for row in result:
		if row[0] not in all_groups:
			all_groups.append(row[0])

	query = "SELECT groupname FROM groups WHERE username=?"
	result = cursor.execute(query, (current_user,))
	groups = []

	for row in result:
		groups.append(row[0])

	# Obtaining all messages for groups to which user belongs.
	placeholder= '?' # For SQLite. See DBAPI paramstyle.
	placeholders= ', '.join(placeholder for unused in groups)
	query = 'SELECT * FROM messages WHERE group_ IN (%s)' % placeholders
	result = cursor.execute(query, groups)

	messages = []

	for row in result:
		messages.append({'name':row[0], 'message_content':row[1], 'likes':row[2], 'dislikes':row[3], 'group_':row[4], 'creator':row[5], 'date_created':row[6]})

	connection.close()


	return render_template('messages.html', messages=messages, groups=groups, all_groups=all_groups)


# Message Form Class
class MessageForm(Form):
    name = StringField('Title', [validators.Length(min=4, max=100)])
    # email = StringField('Email', [validators.Length(min=6, max=50)])
    message_content = TextAreaField('Body', [validators.Length(min=5)])
    group_ = StringField('Group', [validators.Length(min=4, max=50)])


# Add Message
@app.route('/add_message', methods=['GET', 'POST'])
@is_logged_in
def add_message():
	current_user = session['username']
	connection = sqlite3.connect('message_board.db')
	cursor = connection.cursor()

	# Obtaining the groups that the current user belongs to.
	query = "SELECT groupname FROM groups WHERE username=?"
	result = cursor.execute(query, (current_user,))
	groups = []

	for row in result:
		groups.append(row[0])

	form = MessageForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		message_content = form.message_content.data
		likes = 0
		dislikes = 0 
		group_ = form.group_.data
		current_user = session['username']
		global date_time

		# Checking if message with same title exists
		query = "SELECT * FROM messages WHERE name=?" # Name is unique
		result = cursor.execute(query, (name,))
		row=result.fetchone()
		if row:
			connection.close()
			flash('Message with same title already exists.', 'danger')
			
		else:
			if group_ in groups:
				query = "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?)"
				cursor.execute(query, (name, message_content, likes, dislikes, group_, current_user, date_time))

				connection.commit()
				flash('Message posted', 'success')

				connection.close()
				return redirect(url_for('messages'))

			else:
				flash('You are, currently, not a member of this group. Please join.', 'danger')

	connection.close()

	return render_template('add_message.html', form=form)

# Vote
@app.route('/upvote/<string:id>', methods=['POST'])
@is_logged_in
def upvote(id):
	current_user = session['username']
	name=id
	global user_liked
	global user_disliked

	if user_liked != current_user:
		connection = sqlite3.connect('message_board.db')
		cursor = connection.cursor()

		query = "UPDATE messages SET likes=likes+1 WHERE name=?"
		cursor.execute(query, (name,))
		connection.commit()

		if user_disliked == current_user:
			query = "UPDATE messages SET dislikes=dislikes-1 WHERE name=?"
			cursor.execute(query, (name,))
			connection.commit()

		connection.close()

		user_liked = current_user
		user_disliked = ""

	return redirect(url_for('messages'))

# Vote
@app.route('/downvote/<string:id>', methods=['POST'])
@is_logged_in
def downvote(id):
	current_user = session['username']
	name=id

	global user_liked
	global user_disliked

	if user_disliked != current_user:
		connection = sqlite3.connect('message_board.db')
		cursor = connection.cursor()

		query = "UPDATE messages SET dislikes=dislikes+1 WHERE name=?"
		cursor.execute(query, (name,))
		connection.commit()

		if user_liked == current_user:
			query = "UPDATE messages SET likes=likes-1 WHERE name=?"
			cursor.execute(query, (name,))
			connection.commit()

		connection.close()

		user_disliked = current_user
		user_liked = ""

	return redirect(url_for('messages'))

# Delete
@app.route('/delete_message/<string:id>', methods=['POST'])
@is_logged_in
def delete_message(id):
	current_user = session['username']
	name = id

	connection = sqlite3.connect('message_board.db')
	cursor = connection.cursor()

	query = "DELETE FROM messages WHERE name=? and creator=?"
	cursor.execute(query, (name, current_user))

	connection.commit()
	connection.close()

	#flash('Message deleted.', 'success')

	return redirect(url_for('messages'))


# Join Group
@app.route('/join_group/<string:id>', methods=['POST'])
@is_logged_in
def join_group(id):
	current_user = session['username']
	groupname = id

	connection = sqlite3.connect('message_board.db')
	cursor = connection.cursor()

	# Checking if user is not already in group
	query = "SELECT * FROM groups WHERE groupname=? and username=?"
	result = cursor.execute(query, (groupname, current_user,))
	row=result.fetchone()
	if row:
		flash('You are already in the group', 'danger')
		return redirect(url_for('messages'))
	else:
		query = "INSERT INTO groups VALUES (?, ?)"
		cursor.execute(query, (groupname, current_user))

		connection.commit()
		connection.close()

		flash('You have joined the group '+groupname+'.', 'success')

	return redirect(url_for('messages'))


# Leave Group
@app.route('/leave_group/<string:id>', methods=['POST'])
@is_logged_in
def leave_group(id):
	current_user = session['username']
	groupname = id

	connection = sqlite3.connect('message_board.db')
	cursor = connection.cursor()

	query = "DELETE FROM groups WHERE groupname=? and username=?"
	cursor.execute(query, (groupname, current_user))

	connection.commit()
	connection.close()

	flash('You have left the group '+groupname+'.', 'success')

	return redirect(url_for('messages'))



#api.add_resource(Message, '/message/<string:name>')
#api.add_resource(Messages, '/messages')
#api.add_resource(Groups, '/groups/<string:name>')
#api.add_resource(UserRegister, '/register')


if __name__ == '__main__':
    app.run(port=5000, debug=True)