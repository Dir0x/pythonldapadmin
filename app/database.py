import sqlite3, os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../app.db')
connection = sqlite3.connect(db_path)
cursor = connection.cursor()
print("hola")
cursor.execute('''create table if not exists events (id integer primary key autoincrement, timestamp text, type text, do_user text)''')
cursor.execute('''create table if not exists add_object (id integer primary key autoincrement, full_dn text, ldif text, type text, event_id integer, foreign key(event_id) references events(id))''')
cursor.execute('''create table if not exists move_object (id integer primary key autoincrement, original text, cn text, destination text, event_id integer, foreign key(event_id) references events(id))''')
cursor.execute('''create table if not exists modifications (id integer primary key autoincrement, modified_user text, new_ldif text, old_ldif text, event_id integer, foreign key(event_id) references events(id))''')
cursor.execute('''create table if not exists delete_object (id integer primary key autoincrement, full_dn text,event_id integer, foreign key(event_id) references events(id))''')

connection.commit()
connection.close()