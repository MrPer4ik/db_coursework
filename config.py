import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://ka7619:AvadaKedavra18@zanner.org.ua:33321/ka7619'
    #SQLALCHEMY_DATABASE_URI = 'mysql://ka7619:AvadaKedavra18@10.35.2.26:33321/ka7619'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CARDS_PER_PAGE = 15
