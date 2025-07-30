import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-aqui'

    # Banco de dados (usando SQLite na pasta instance/)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'cashflex.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # E-mail (ajuste conforme seu provedor)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'seu-email@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'sua-senha-de-central-ou-conta'
    MAIL_DEFAULT_SENDER = MAIL_USERNAME