from app import app
from flask import session, request, render_template, url_for, redirect, flash
import ldap, time
from passlib.hash import ldap_md5_crypt
import ldap.modlist as modlist

# To do
# Mover usuarios entre OUs
# Añadir OUs

@app.route('/login',methods=['GET', 'POST'])
def login():
	if request.method == "POST":
		login_username = request.form['user']
		login_password = request.form['password']
		address = request.form['address']
		login_domain = "dc=" + request.form['domain'].replace(".", ",dc=")

		try:
			l = ldap.initialize("ldap://" + address)
			bind = l.simple_bind_s("cn=" + login_username + "," + login_domain, login_password)
			if str(bind) == "(97, [], 1, [])":
				session['user'] = login_username
				session['address'] = address
				session['password'] = login_password
				session['address'] = address
				session['domain'] = login_domain
				flash("Logged in as: " + session['user'])
				l.unbind_s()
				return redirect(url_for('home'))
		except ldap.INVALID_CREDENTIALS:
			flash("Invalid credentials")
		except ldap.SERVER_DOWN:
			flash("Can't contact LDAP server")
		return redirect(url_for('login'))
	else:
		if not 'user' in session:
			return render_template('login.html')
		else:
			return redirect(url_for('home'))

@app.route('/logout', methods=['GET'])
def logout():
	session.clear()
	return redirect(url_for('home'))

@app.route('/modify_user/<name>', methods=['GET', 'POST'])
def modify_user(name):
	value = ""
	if 'user' in session:
		if request.method == "GET":
			l = ldap.initialize("ldap://" + session['address'])
			bind = l.simple_bind_s("cn=" + session['user'] + "," + session['domain'], session['password'])
			result = l.search_s(name, ldap.SCOPE_SUBTREE, "objectClass=*", ['*'])
			l.unbind_s()

			for item in result[0][1]:
				value += '<label>' + item + ': <input type="text" name="' + item + '" value="' + str(result[0][1].get(item)) + '"/></label></br>'

		elif request.method == "POST":
			try:
				l = ldap.initialize("ldap://" + session['address'])
				bind = l.simple_bind_s("cn=" + session['user'] + "," + session['domain'], session['password'])
				new_ldif = request.form.to_dict(flat=False)
				old_ldif = l.search_s(name, ldap.SCOPE_SUBTREE, "objectClass=*", ['*'])[0][1]

			except:
				flash("Can't contact LDAP server")
				return redirect(url_for('home'))

			try:
				diff_new = {}
				diff_old = {}

				for item in new_ldif:
					if str(new_ldif[item][0]) == str(old_ldif[item]):
						pass
					else:
						if item == "cn":
							l.modrdn_s(name, 'cn=' + new_ldif[item][0][:-2][3:], True)
							name = name.replace(name.split(",")[0], "cn=" + new_ldif[item][0][:-2][3:])

						else:
							i = []
							i.append(bytes(new_ldif[item][0][:-2][3:], 'UTF-8'))
							diff_new[item] = i

							i = []
							i.append(old_ldif[item][0])
							diff_old[item] = i
				
				ldif = modlist.modifyModlist(diff_old, diff_new)
				l.modify_s(name,ldif)
				l.unbind_s()

				flash("Modification performed")
				return redirect(url_for('home'))

			except:
				flash("Unable to perform the modification")
				return redirect(url_for('home'))

	else:
		flash("You must authenticate")
		return redirect(url_for('login'))

	return render_template("modify_user.html", value=value)

@app.route('/create_object')
def create_object():
	return render_template("create_object.html")

@app.route('/add_user', methods=['POST'])
def add_user():
	fullname = request.form['username']
	home_dir = request.form['home']
	gid = request.form['gid']
	shell = request.form['shell']
	password1 = request.form['password1']
	password2 = request.form['password2']
	uid = request.form['uid']

	if password1 != password2:
		flash("Las contraseñas deben coincidir")
		return redirect(url_for('create_object'))

	hash = ldap_md5_crypt.hash(password1)
	entry = []
	entry.extend([
		('objectClass', [b"inetOrgPerson", b"organizationalPerson", b"posixAccount", b"person"]),
		('uid', bytes(uid, 'UTF-8')),
		('sn', bytes(fullname, 'UTF-8')),
		('uidNumber', b"2000"),
		('gidNumber', bytes(gid, 'UTF-8')),
		('loginShell', bytes(shell, 'UTF-8')),
		('homeDirectory', bytes(home_dir, 'UTF-8')),
		('userPassword', bytes(hash, 'UTF-8'))
	])

	try:
		l = ldap.initialize("ldap://" + session['address'])
		bind = l.simple_bind_s("cn=" + session['user'] + "," + session['domain'], session['password'])
	except:
		flash("Can't connect to LDAP server")
		return redirect(url_for('create_object'))

	if 'parent' in request.form:
		parent = request.form['parent']

	else:
		parent = session['domain']

	try:
		l.add_s("cn=" + fullname + "," + parent, entry)
		l.unbind_s()
		flash("User added")
		return redirect(url_for('home'))

	except:
		flash("Couldn't create the user")
		return redirect(url_for('home'))

@app.route("/add_group", methods=['POST'])
def add_group():
	try:
		l = ldap.initialize("ldap://" + session['address'])
		bind = l.simple_bind_s("cn=" + session['user'] + "," + session['domain'], session['password'])
	except:
		flash("Can't connect to LDAP server")
		return redirect(url_for('home'))
		
	if 'parent' in request.form:
		parent = request.form['parent']

	else:
		parent = session['domain']
		
	entry = [('objectClass', [b'posixGroup', b'top']), 
				('cn', [bytes(request.form['cn'], 'UTF-8')]), 
				('gidNumber', [bytes(request.form['gid'], 'UTF-8')])]

	try:
		l.add_s("cn=" + request.form['cn'] + "," + parent ,entry)
		l.unbind_s()
		flash("Group created")
		return redirect(url_for('home'))

	except:
		flash("An error occurred")
		return redirect(url_for('home'))

	return parent

@app.route("/delete_user", methods=['POST'])
def delete_user():
	if request.form['user']:
		try:
			try:
				l = ldap.initialize("ldap://" + session['address'])
				bind = l.simple_bind_s("cn=" + session['user'] + "," + session['domain'], session['password'])
			except:
				flash("Can't connect to LDAP server")
				return redirect(url_for('home'))

			try:
				l.delete(request.form['user'])
				l.unbind_s()
				flash("User deleted")
				time.sleep(1)
				return redirect(url_for('home'))
			except:
				flash("Unable to delete the user")
				return redirect(url_for('home'))

		except:
			flash("An error occurred")
			return redirect(url_for('delete_user'))


@app.route("/", methods=['GET'])
def home():
	if 'user' in session:
		response = ""
		l = ldap.initialize("ldap://" + session['address'])
		results = l.search_s(session['domain'], ldap.SCOPE_SUBTREE, "objectClass=*", [''])
		
		new_results = []

		for result in results:
			new = []
			old = result[0].split(',')
			for i in range(len(old)):
				new.insert(0, old[i])
			new_results.append(new)
		results = sorted(new_results)

		last = 0
		parents = []
		tags = []

		for result in results:
			printable = ""
			inverted = ""

			for i in range(len(result)):
				inverted = str(result[i]) + "," + inverted
			inverted = inverted[:-1]

			if len(result) == 2:
				printable = inverted
			else:
				printable = result[len(result)-1]

			if printable.startswith('cn='):
				printable += " <a href='modify_user/" + inverted + "'>Modify" '</a><form action="/delete_user" method="POST">\n	<input type="hidden" name="user" value="' + inverted + '">\n    <input type="image" src="https://cdn-icons-png.flaticon.com/512/58/58326.png" alt="submit" width="20" height="20">\n</form>'
			else:
				if len(result) == 2:
					printable = " <a href='modify_user/" + inverted + "'>" + printable + '</a>'
				else:
					printable += " <a href='modify_user/" + inverted + "'>Modify" '</a><form action="/delete_user" method="POST">\n	<input type="hidden" name="user" value="' + inverted + '">\n    <input type="image" src="https://cdn-icons-png.flaticon.com/512/58/58326.png" alt="submit" width="20" height="20">\n</form>'

			if len(result) == 2:
				response += "<ul><li>" + printable
				tags.insert(0, "</ul>")
				tags.insert(0, "</li>")

			elif len(result) > last:
				parents.insert(0, last_item)
				response += "<ul><li>" + printable
				tags.insert(0, "</ul>")
				tags.insert(0, "</li>")

			elif len(result) == last:
				response += "</li><li>" + printable

			elif len(result) < last:
				response += "</li><a href='/create_object?parent=" + parents[0] + "'>Add child object</a></ul></li><li>" + printable
				parents.pop(0)
				tags.remove("</li>")
				tags.remove("</ul>")
				tags.remove("</li>")
				tags.insert(0, "</li>")

			last_item = inverted
			last = len(result)

		while len(tags) != 0:
			if len(tags) > 1:
				if str(tags[0]) == "</ul>":
					insert = "<li><a href='/create_object?parent=" + parents[0] + "'>Add child object</a></li>" + tags[0]
					parents.pop(0)
				else:
					insert = tags[0]
				response += insert + "\n"
				tags.remove(tags[0])
			else:
				response += tags[0] + "\n"
				tags.remove(tags[0])

		return render_template('index.html', user=session['user'], tree=response)
	else:
		flash("You must authenticate")
		return redirect(url_for('login'))