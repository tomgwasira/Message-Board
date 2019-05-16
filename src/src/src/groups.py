import sqlite3
from flask import Flask, request
from flask_restful import Resource


class Groups(Resource):
    
    # /groups/<string:name> - Determining which groups a particular user is in. The user is given by <string:name>
    def get(self, name):
        connection = sqlite3.connect('message_board.db')
        cursor = connection.cursor()

        query = "SELECT groupname FROM groups WHERE username=?" # Selects all group names for which the user is a member.
        result = cursor.execute(query, (name,))
        groups = []

        for row in result:
            groups.append(row[0])

        connection.close()

        return {name:groups}


    def post(self, name):  # Exactly same parameters as get
        # Checking if the group-username mapping already exists
        connection = sqlite3.connect('message_board.db')
        cursor = connection.cursor()

        data = request.get_json()
        group = {'groupname':data['groupname'], 'username':name}

        query1 = "SELECT * FROM groups WHERE groupname=? and username=?" # Selects all group names for which the user is a member.
        result = cursor.execute(query1, (group['groupname'], name))
        row = result.fetchone()

        if not row:    
            query2 = "INSERT INTO groups VALUES (?, ?)"
            cursor.execute(query2, (group['groupname'], name))

            connection.commit()
            connection.close()

            return group, 201
        return {'status': 'User already in given group'}, 404


    # /groups/<string:name>/<string:groupname> - Deleting a user from a group
    def delete(self, name, groupname):
        connection = sqlite3.connect('message_board.db')
        cursor = connection.cursor()

        query = "DELETE FROM groups WHERE groupname=? and username=?"
        cursor.execute(query, (groupname, name))

        connection.commit()
        connection.close()

        return {'status': 'message deleted'}





