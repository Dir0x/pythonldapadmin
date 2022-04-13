from app import app
from flask import session, request
import ldap

base = "dc=dharo, dc=local"

@app.route('/login',methods=['GET', 'POST'])
def login():
	response = ""
	if request.method == "POST":
		login_username = request.form['user']
		login_password = request.form['password']
		address = request.form['address']
		
		try:
			l = ldap.initialize("ldap://" + address)
			bind = l.simple_bind_s("cn=" + login_username + "," + base, login_password)
			if str(bind) == "(97, [], 1, [])":
				session['user'] = login_username
				session['address'] = address
				session['bind'] = bind
				session['address'] = address
				response = response + session['user']
		except:
			response = response + "Invalid credentials"
	if not 'user' in session:
		response = response + "<form method='POST'><input type='text' name='user'/><input type='password' name='password'/><input type='text' name='address'/><input type='submit'/></form>"

	response = response + " hola" 
	return response

@app.route("/", methods=['GET'])
def home():
	response = ""
	if 'bind' in session:
		l = ldap.initialize("ldap://" + session['address'])
		results = l.search_s(base, ldap.SCOPE_SUBTREE, "objectClass=*", [''])
		
		dn_base =  'dc=dharo,dc=local'
		new_results = []

		for result in results:
			new = []
			old = result[0].split(',')
			for i in range(len(old)):
				new.insert(0, old[i])
			new_results.append(new)
		results = sorted(new_results)

		last = 0
		tags = []

		for result in results:
			printable = ""

			for i in range(len(result)):
				printable = str(result[i]) + "," + printable

			printable = printable[:-1]

			if len(result) == 2:
				response += "<ul><li>" + printable
				tags.insert(0, "</ul>")
				tags.insert(0, "</li>")
			elif len(result) > last:
				response += "<ul><li>" + printable
				tags.insert(0, "</ul>")
				tags.insert(0, "</li>")
			elif len(result) == last:
				response += "</li><li>" + printable
			elif len(result) < last:
				response += "</li></ul></li><li>" + printable
				tags.remove("</li>")
				tags.remove("</ul>")
				tags.remove("</li>")
				tags.insert(0, "</li>")
			last = len(result)

		while len(tags) != 0:
			response += tags[0]
			tags.remove(tags[0])

		return response
	else:
		return "you must authenticate"
