class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'q'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:1234@localhost/timbreuse'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
