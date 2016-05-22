from flask import Flask, \
	render_template
from flask_sqlalchemy import SQLAlchemy
from config import DevelopmentConfig as Config
from flask.ext.login import LoginManager

from flask import Flask, session, request, flash, url_for, redirect, render_template, abort, g
from flask.ext.login import login_user, logout_user, current_user, login_required


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

from models import *

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
	return render_template('index.html')

# ============================================================
#                       Authentication shit
# ============================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    user = User(request.form['username'], request.form['password'])
    db.session.add(user)
    db.session.commit()
    flash('User successfully registered')
    return redirect(url_for('login'))


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']
    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True
    registered_user = User.query.filter_by(username=username,password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid' , 'error')
        return redirect(url_for('login'))
    login_user(registered_user, remember = remember_me)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# ============================================================
#                       User shit
# ============================================================
@app.route('/users/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    projects = user.projects
    if request.method == 'GET':
        return render_template('users/index.html', user=user, projects=projects)



# ============================================================
#                       Project shit
# ============================================================
@app.route('/new', methods=['GET', 'POST'])
def new_project():
    if request.method == 'GET':
        return render_template('projects/new.html')
    elif request.method == 'POST':
        project = Project(request.form['name'])
        current_user.projects.append(project)
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('user', username=current_user.username))

if __name__ == '__main__':
	app.run()
