from flask import Flask, \
	render_template
from flask_sqlalchemy import SQLAlchemy
from config import DevelopmentConfig as Config
from flask.ext.login import LoginManager

from flask import Flask, session, request, flash, url_for, redirect, render_template, abort, g
from flask.ext.login import login_user, logout_user, current_user, login_required

import datetime


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
        current_project_id = current_user.current_project_id
        current_project = Project.query.filter_by(id=current_project_id).first()
        if current_project_id is not None:
            tasks = Task.query.filter_by(project_id=int(current_project_id)).all()
        current_timeslot = active_timeslot()
        if current_timeslot is not None:
            current_task = Task.query.filter_by(id=current_timeslot.task_id).first().name
        return render_template('home.html', **locals())
    else:
        return render_template('index.html')


# ============================================================
#                       Authentication shit
# ============================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.form['username'] in (u.username for u in User.query.all()):
        flash('username invalid')
        return redirect(request.referrer)
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

    registered_user = User.query.filter_by(username=username).first()
    if registered_user is None or not registered_user.check_password(password):
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
        if len(request.form['project_name']) > 50:
            flash('The name for your project is too long. 50 chars max.')
            return redirect(request.referrer)
        project = Project(request.form['project_name'])
        current_user.projects.append(project)
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('index'))


@app.route('/project/<project_id>')
@login_required
def project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    tasks = Task.query.filter_by(project_id=project.id).all()
    timeslots = []
    for t in tasks:
        timeslots[len(timeslots):] = [x for x in t.timeslots]
    timeslots = sorted(timeslots, key=lambda x: x.started_at)
    timeslots = [(t, Task.query.filter_by(id=int(t.task_id)).first()) for t in timeslots]
    return render_template('projects/show.html', **locals())


@app.route('/select', methods=['POST'])
@login_required
def select_shit():
    current_project = request.form['current_project']
    projects = current_user.projects

    # cuz maybe user edited the html in the hidden input value
    # so we still check values, yo
    if int(current_project) not in (int(p.id) for p in projects):
        flash('Don\'t fuck with us')
        return redirect(request.referrer)
    
    current_user.current_project_id = current_project
    db.session.commit()

    project = Project.query.filter_by(id=current_project).first().name
    flash(u'Now working on {}'.format(project))
    return end_timeslot()


# ============================================================
#                       Task shit
# ============================================================
@app.route('/newtask', methods=['GET', 'POST'])
@login_required
def new_task():
    if request.method == 'GET':
        return render_template('tasks/new.html')
    elif request.method == 'POST':
        if len(request.form['task_name']) > 50:
            flash('The name for your task is too long. 50 chars max.')
            return redirect(request.referrer)
        task = Task(request.form['task_name'], request.form['task_comment'])
        project = Project.query.filter_by(id=int(current_user.current_project_id)).first()
        project.tasks.append(task)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('index'))


@app.route('/task/<task_id>')
@login_required
def show_task(task_id):
    task = Task.query.filter_by(id=task_id).first_or_404()
    project = Project.query.filter_by(id=task.project_id).first()
    if project.user_id != current_user.id:
        flash('You fucker won\'t spy')
        logout_user()
        return redirect(url_for('index'))
    timeslots = TimeSlot.query.filter_by(task_id=task.id).all()
    return render_template('tasks/show.html', **locals())


@app.route('/newshit', methods=['POST'])
@login_required
def new_shit():
    if current_user.current_project_id is None:
        flash('Please activate a project')
        return redirect(url_for('index'))

    task_id = request.form['select_task']
    task = Task.query.filter_by(project_id=int(current_user.current_project_id)).filter_by(id=task_id).first()
    if task is None:
        task = Task(taskname, '')
        project = Project.query.filter_by(id=int(current_user.current_project_id)).first()
        project.tasks.append(task)
        db.session.add(task)
        flash(u'Added task {} to project {}'.format(taskname, project.name))

    lasttime = TimeSlot.query.filter_by(ended_at=None).first()
    if lasttime is not None:
        lasttime.ended_at = datetime.datetime.now()
        flash(u'Previous time slot ended')

    now = TimeSlot(request.form['comment'], datetime.datetime.now())
    task.timeslots.append(now)
    db.session.commit()
    flash(u'Time slot added to task {}'.format(task.name))

    return redirect(request.referrer)


@app.route('/edittaskcomment/<task_id>', methods=['POST'])
@login_required
def edit_task_comment(task_id):
    task = Task.query.filter_by(id=task_id).first_or_404()
    tasks = []
    for p in current_user.projects:
        tasks[len(tasks):] = [int(t.id) for t in p.tasks]
    if int(task_id) not in tasks:
        flash('I don\'t like you')
        logout_user()
        return redirect(url_for('index'))
    
    task.description = request.form['description']
    db.session.commit()
    flash('Updated description')

    return redirect(request.referrer)


@app.route('/edittimeslotcomment/<timeslot_id>', methods=['POST'])
@login_required
def edit_timeslot_comment(timeslot_id):
    timeslot = TimeSlot.query.filter_by(id=timeslot_id).first_or_404()
    timeslots = []
    for p in current_user.projects:
        for t in p.tasks:
            timeslots[len(timeslots):] = [int(x.id) for x in t.timeslots]
    if int(timeslot_id) not in timeslots:
        flash('GTFO you hacker')
        logout_user()
        return redirect(url_for('index'))
    
    timeslot.comment = request.form['comment']
    db.session.commit()
    flash('Updated comment')

    return redirect(request.referrer)


@app.route('/endtimeslot', methods=['POST'])
@login_required
def end_timeslot():
    current_timeslot = active_timeslot()
    if current_timeslot is None:
        return redirect(url_for('index'))
    current_timeslot.ended_at = datetime.datetime.now()
    db.session.commit()
    flash('Timeslot ended')

    return redirect(url_for('index'))


# ============================================================
#                       random
# ============================================================
def active_timeslot():
    current_timeslots = TimeSlot.query.filter_by(ended_at=None).all()
    timeslots = []
    for p in current_user.projects:
        for t in p.tasks:
            timeslots[len(timeslots):] = [int(x.id) for x in t.timeslots]
    
    for t in current_timeslots:
        for u in timeslots:
            if int(t.id) == u:
                return t
    else:
        return None


if __name__ == '__main__':
	app.run()
