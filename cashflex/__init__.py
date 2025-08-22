from flask import Flask, jsonify   # <-- adicione o jsonify aqui
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from cashflex.config import Config
import os
import logging

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
    from cashflex.routes.main import main
    from cashflex.routes.admin import admin
    from cashflex.routes.plan import plan
    from cashflex.routes.utils.task import tasks_bp

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
        from cashflex.models import User
        return User.query.get(int(user_id))

    # Registro de erros no log
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    @app.errorhandler(Exception)
    def log_exception(e):
        app.logger.exception("❌ Erro não tratado detectado:")
        return "Erro interno do servidor", 500

    # 🔥 Importante: Handler para requisições AJAX não autenticadas
    @login_manager.unauthorized_handler
    def unauthorized_callback():
        # Para requisições AJAX, retorne JSON em vez de HTML
        return jsonify({"error": "Sessão expirada. Faça login novamente."}), 401

    return app
