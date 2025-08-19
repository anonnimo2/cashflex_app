
import random
import string
from datetime import datetime
from cashflex import db  # usa o db criado em __init__.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------- MODELO: USUÁRIO -------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=500.0)
    invite_code = db.Column(db.String(10), unique=True)
    referred_by = db.Column(db.String(10), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    bank = db.Column(db.String(50), nullable=True)
    iban = db.Column(db.String(25))  # IBAN angolano tem 23-25 caracteres
    iban_owner = db.Column(db.String(100))  # Nome do titular da conta

    # Relacionamentos
    investments = db.relationship('Investment', backref='user', lazy=True)
    withdrawals = db.relationship('Withdrawal', backref='user', lazy=True)
    planos = db.relationship('UserPlan', backref='user', lazy=True)
    deposits = db.relationship('Deposit', backref='user', lazy=True)
    def has_active_plan(self):
        return any(plan.ativo for plan in self.planos)

    def has_withdrawn_today(self):
        today = datetime.utcnow().date()
        last_withdrawal = Withdrawal.query.filter_by(user_id=self.id).order_by(Withdrawal.timestamp.desc()).first()
        return last_withdrawal and last_withdrawal.timestamp.date() == today

    def has_pending_withdrawal(self):
        return any(w.status == 'Pendente' for w in self.withdrawals)

    def get_referrals(self, level=1):
        if level == 1:
            return User.query.filter_by(referred_by=self.invite_code).all()
        elif level == 2:
            level1 = self.get_referrals(1)
            return [u for user in level1 for u in User.query.filter_by(referred_by=user.invite_code).all()]
        elif level == 3:
            level2 = self.get_referrals(2)
            return [u for user in level2 for u in User.query.filter_by(referred_by=user.invite_code).all()]
        return []

    @property
    def total_profit(self):
        return sum(p.profit for p in self.planos if p.ativo)

    @property
    def planos_ativos(self):
        return [p for p in self.planos if p.ativo]

    def set_password(self, password_plain):
        self.password = generate_password_hash(password_plain)

    def check_password(self, password_plain):
        return check_password_hash(self.password, password_plain)

    def __repr__(self):
        return f"<User {self.phone}>"

# ------------------- MODELO: PLANO DO USUÁRIO -------------------

class UserPlan(db.Model):
    __tablename__ = 'user_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    investimento = db.Column(db.Float, nullable=False)
    rendimento_diario = db.Column(db.Float, nullable=False)  # 10% do investimento
    retorno_total = db.Column(db.Float, nullable=False)  # Ex: investimento * 5.0

    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_credito = db.Column(db.DateTime)
    ativo = db.Column(db.Boolean, default=True)
    dias_pagamentos = db.Column(db.Integer, default=0)
    recebido = db.Column(db.Float, default=0.0)

    @property
    def profit(self):
        return round(self.rendimento_diario * self.dias_pagamentos, 2)

    def __repr__(self):
        return f"<Plano {self.nome} de {self.user_id}>"

# ------------------- MODELO: INVESTIMENTO -------------------

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    proof = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Pendente')
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<Investimento {self.amount} por {self.user_id}>"

# ------------------- MODELO: SAQUE -------------------

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pendente')
    bank = db.Column(db.String(10))  # Banco selecionado
    iban = db.Column(db.String(34))  # IBAN informado
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    taxa = db.Column(db.Float, default=0.0)           # valor da taxa cobrada
    valor_liquido = db.Column(db.Float, default=0.0)  # valor após desconto


    def __repr__(self):
        return f"<Saque {self.amount} de {self.user_id}>"

# ------------------- MODELO: COMISSÃO -------------------


class InvestmentPlan(db.Model):
    __tablename__ = 'investment_plan'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)                # Nome do plano (ex: VIP-1)
    valor = db.Column(db.Float, nullable=False)                    # Novo campo "valor"
    invest = db.Column(db.Float, nullable=False)                   # Valor de investimento inicial
    rendimento_diario = db.Column(db.Float, nullable=False)        # Lucro diário
    retorno_total = db.Column(db.Float, nullable=False)            # Valor total a receber
    ativo = db.Column(db.Boolean, nullable=False, default=True) 
    valor_minimo = db.Column(db.Float, nullable=False)
    def __repr__(self):
        return f"<InvestmentPlan {self.nome}>"

    @property
    def rendimento(self):
        return self.rendimento_diario

    @property
    def retorno(self):
        return self.retorno_total

class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    bank = db.Column(db.String(50))
    proof = db.Column(db.String(120))
    status = db.Column(db.String(20), default='Pendente')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)



class Commission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # quem recebeu
    from_user_id = db.Column(db.Integer)  # quem originou a comissão
    level = db.Column(db.Integer)  # nível da comissão: 1, 2 ou 3
    amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<Comissão nível {self.level} para {self.user_id}>"

# ------------------- FUNÇÕES AUXILIARES -------------------

def generate_unique_code(length=6):
    while True:
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        if not User.query.filter_by(invite_code=code).first():
            return code

def distribuir_comissao(investimento):
    user = User.query.get(investimento.user_id)
    comissoes = [0.25, 0.04, 0.01]
    ref_code = user.referred_by

    for nivel in range(3):
        if not ref_code:
            break
        padrinho = User.query.filter_by(invite_code=ref_code).first()
        if padrinho:
            valor_comissao = investimento.amount * comissoes[nivel]
            padrinho.balance += valor_comissao

            com = Commission(
                user_id=padrinho.id,
                from_user_id=user.id,
                level=nivel + 1,
                amount=valor_comissao
            )
            
            db.session.add(com)
            db.session.add(padrinho)
            ref_code = padrinho
           
class JobLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(100), nullable=False)
    run_date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)