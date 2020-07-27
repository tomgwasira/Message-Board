# Message Forum

Install:
- flask
- WTForms
- Flask-RESTful
- passlib

Notes:
- Ensure there is no database (named message-board.db) in project/src/src. Delete if one currently exists.
- From command line, navigate into project/src/src directory.
- Run python db_creation.py  (This will initialise a database and create some sample groups. Create new or delete groups if necessary).
- Run python app.py

- The delete function is written to work only if the currently logged in user is the one that posted the message.


