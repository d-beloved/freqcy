import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
  DEBUG = False
  TESTING = False
  CSRF_ENABLED = True
  SECRET_KEY = 'gonna change this soon'

class ProductionConfig(Config):
  DEBUG = False

class DevelopmentConfig(Config):
  DEVELOPMENT = True
  DEBUG = False

class TestingConfig(Config):
  TESTING = True