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
    if current_user.is_authenticated:
        current_project = Project.query.filter_by(id=current_user.current_project)
        return render_template('home.html', current_project=current_project)
    else:
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


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True

    registered_user = User.query.filter_by(username=username, password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid' , 'error')
        return redirect(url_for('login'))
    login_user(registered_user, remember=remember_me)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# ============================================================
#                       Project shit
# ============================================================
@app.route('/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'GET':
        return render_template('projects/new.html')
    elif request.method == 'POST':
        project = Project(request.form['project_name'])
        current_user.projects.append(project)
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('index'))


@app.route('/project/<project_id>')
@login_required
def project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    return render_template('projects/show.html', project=project)


@app.route('/select', methods=['POST'])
@login_required
def select_shit():
    current_project = request.form['current_project']
    projects = current_user.projects

    # cuz maybe user edited the html in the hidden input value
    # so we still check values, yo
    if int(current_project) not in (int(p.id) for p in projects):
        flash('Don\'t fuck with us')
    else:
        current_user.current_project = current_project
        db.session.commit()

        project = Project.query.filter_by(id=current_project).first().name
        flash(u'Now working on {}'.format(project))
    return redirect(url_for('project', project_id=current_user.current_project))


@app.route('/newshit', methods=['GET', 'POST'])
@login_required
def new_shit():
    if request.method == 'POST':
        if current_user.current_project == None:
            redirect(url_for('select_shit'))

        task = request.form['newshit']

        tasks = Task.query.filter_by(project_id=int(current_user.current_project)).all()
        if task not in (t.name for t in tasks):
            newtask = Task(task, '')
            project = Project.query.filter_by(id=int(current_user.current_project)).first()
            project.tasks.append(newtask)
            db.session.add(newtask)
            db.session.commit()
        flash(u'Time slot added to task {} in project {}'.format(task, 'placeholder'))

    return render_template('projects/newshit.html')


if __name__ == '__main__':
	app.run()
