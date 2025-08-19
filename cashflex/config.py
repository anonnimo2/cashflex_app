import os
from dotenv import load_dotenv
load_dotenv()  # Carrega as variáveis do .env antes de usar

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-aqui'

    # Banco de dados
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:iIGkeYGNrtiuAaMtWAoMPNSeFZpsEUFV@postgres.railway.internal:5432/railway'

    print(f"[INFO] Banco de dados usado: {SQLALCHEMY_DATABASE_URI}")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # E-mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'manecomonteirofino@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '@Anonimo22'
    MAIL_DEFAULT_SENDER = MAIL_USERNAME

    # Pasta de uploads (caminho absoluto)
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'proofs')
