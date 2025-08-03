from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from app.config import Config
from datetime import datetime
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

login_manager.login_view = 'main.login'
login_manager.login_message = 'Faça login para acessar esta página.'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Registrar blueprints
    from app.routes.main import main
    from app.routes.admin import admin
    from app.routes.plan import plan
    from app.routes.utils.task import tasks_bp

    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(plan)
    app.register_blueprint(tasks_bp)

    # Config pasta de upload
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'proofs')

    # Variável global
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.now().year}

    # Carregamento de usuário
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    return app