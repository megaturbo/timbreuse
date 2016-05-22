from config import Config
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from timbreuse import app, db
from models import *

app.config.from_object(Config)

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


@manager.command
def drop():
    db.drop_all()
    

if __name__ == '__main__':
    manager.run()
