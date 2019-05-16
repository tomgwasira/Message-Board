import sqlite3
from flask import Flask, request
from flask_restful import Resource
from flask_jwt import jwt_required, current_identity
from security import authenticate


class Message(Resource):
    
    # /message/<string:name> - Accessing a message. The name is the message title.
    @jwt_required()
    def get(self, name):
        user = current_identity
        current_user = (user.username)

        try: 
            message = self.find_by_name(name, current_user)
            if message:
                return message
        except:
            return {'status': 'An error occured while accessing.'}, 500 # Internal server error.

        return {'status': 'Message not found'}, 404


    # Finding message in database.
    @classmethod
    def find_by_name(cls, name, current_user):
        connection = sqlite3.connect('message_board.db')
        cursor = connection.cursor()

        # Obtaining the groups that the current user belongs to.
        query1 = "SELECT groupname FROM groups WHERE username=?"
        result = cursor.execute(query1, (current_user,))
        groups = []
        for row in result:
            groups.append(row[0])


        query2 = "SELECT * FROM messages WHERE name=?"
        result = cursor.execute(query2, (name,))
        row = result.fetchone()   # Because name is unique.
        
        connection.close()

        if row:
            if row[3] in groups:
                return {'message': {'name':row[0], 'message_content':row[1], 'vote_count':row[2], 'group_':row[3], 'creator':row[4], 'date_created':row[5]}}
            else:
                return {'status':'User not in message group.'}


    # /message/<string:name> - Posting a message.
    @jwt_required()
    def post(self, name):  # Exactly same parameters as get
        user = current_identity
        current_user = (user.username)

        if self.find_by_name(name, current_user):
            return {'status': "A message with title '{}' already exists.".format(name)}, 400 # Bad request. Already in the server.

        data = request.get_json()
        
        message = {'name':name, 'message_content':data['message_content'], 'vote_count':data['vote_count'], 'group_':data['group_'], 'creator':current_user, 'date_created':data['date_created']}
        
        try:
            insertion = self.insert(message, current_user)
            if insertion:
                return message, 201
        except:
            return {'status': 'An error occured during posting of message.'}, 500 # Internal server error.

        return {'status': 'User not in message group.'}
        


    # Insertion into database.
    @classmethod
    def insert(cls, message, current_user):
        connection = sqlite3.connect('message_board.db')
        cursor = connection.cursor()

        # Obtaining the groups that the current user belongs to.
        query1 = "SELECT groupname FROM groups WHERE username=?"
        result = cursor.execute(query1, (current_user,))
        groups = []
        for row in result:
            groups.append(row[0])

        if message['group_'] in groups:
            query = "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)"
            cursor.execute(query, (message['name'], message['message_content'], message['vote_count'], message['group_'], current_user, message['date_created']))

            connection.commit()
            connection.close()
            return {'status': 'Insertion complete.'}



    # /message/<string:name> - Deleting a message.
    @jwt_required()
    def delete(self, name):
        user = current_identity
        current_user = (user.username)

        connection = sqlite3.connect('message_board.db')
        cursor = connection.cursor()

        query = "DELETE FROM messages WHERE name=? and creator=?"
        cursor.execute(query, (name, current_user))

        connection.commit()
        connection.close()

        return {'status': 'message deleted'}

    # /message/<string:name> - Editing a message.
    @jwt_required()
    def put(self, name):
        user = current_identity
        current_user = (user.username)

        data = request.get_json()
        message = self.find_by_name(name, current_user)
        updated_message = {'name':name, 'message_content':data['message_content'], 'vote_count':data['vote_count'], 'group_':data['group_'], 'creator':data['creator'], 'date_created':data['date_created']}

        if message is None:
            try:
                Message.insert(updated_message)
            except:
                return {"status": "An error occurred inserting the message."}
        else:
            try:
                Message.update(updated_message)
            except:
                raise
                return {"status": "An error occurred updating the message."}
        return updated_message, 201



    # Updating of database.
    @classmethod
    def update(cls, message):
        connection = sqlite3.connect('message_board.db')
        cursor = connection.cursor()

        query = "UPDATE messages SET vote_count=? WHERE name=?"
        cursor.execute(query, (message['vote_count'], message['name']))

        connection.commit()
        connection.close()        


class Messages(Resource):
    @jwt_required()
    def get(self):
        user = current_identity
        current_user = (user.username)

        connection = sqlite3.connect('message_board.db')
        cursor = connection.cursor()

        # Obtaining the groups that the current user belongs to.
        query1 = "SELECT groupname FROM groups WHERE username=?"
        result = cursor.execute(query1, (current_user,))
        groups = []
        for row in result:
            groups.append(row[0])

        # Obtaining all messages for groups to which user belongs.
        placeholder= '?' # For SQLite. See DBAPI paramstyle.
        placeholders= ', '.join(placeholder for unused in groups)
        query = 'SELECT * FROM messages WHERE group_ IN (%s)' % placeholders
        result = cursor.execute(query, groups)

        # query = "SELECT * FROM messages"
        # result = cursor.execute(query)
        messages = []
        for row in result:
            messages.append({'name':row[0], 'message_content':row[1], 'vote_count':row[2], 'group_':row[3], 'creator':row[4], 'date_created':row[5]})

        connection.close() 

        return {'messages': messages} 
