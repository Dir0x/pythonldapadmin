from app import app
from flask import session, request, render_template, url_for, redirect, flash
import ldap
from passlib.hash import ldap_md5_crypt

# Crear sección de ajustes para definir variables como directorio de usuarios
# OU por defecto en ajustes
# modo no redirección en los ajustes para que te mande al home o no al añadir usuarios

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

@app.route('/modify/<name>', methods=['GET'])
def modify(name):
	
	return name

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
	if request.method == "GET":
		return render_template('add_user.html')
	elif request.method == "POST":
		fullname = request.form['username']
		home_dir = request.form['home']
		gid = request.form['gid']
		shell = request.form['shell']
		password1 = request.form['password1']
		password2 = request.form['password2']
		uid = request.form['uid']
		if password1 != password2:
			flash("Las contraseñas deben coincidir")
			return redirect(url_for('add_user'))
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
			try:
				l = ldap.initialize("ldap://" + session['address'])
				bind = l.simple_bind_s("cn=" + session['user'] + "," + session['domain'], session['password'])
			except:
				flash("conexión fallida")

			l.add_s("cn=" + fullname + ",dc=dharo,dc=local", entry)
			flash("exito")
			return redirect(url_for('home'))
		except:
			flash("error")
			return redirect(url_for('add_user'))

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
		tags = []

		for result in results:
			printable = ""

			for i in range(len(result)):
				printable = str(result[i]) + "," + printable
			printable = printable[:-1]
			printable = "<a href='modify/" + printable + "'>" + printable + "</a>"

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

		return render_template('index.html', title='Home', user=session['user'], tree=response)
	else:
		flash("You must authenticate")
		return redirect(url_for('login'))