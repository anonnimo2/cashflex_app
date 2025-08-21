from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from cashflex import db
from flask import current_app
from datetime import datetime
from cashflex.forms import LoginForm, RegisterForm, WithdrawalForm, ProfileForm, DepositForm
from cashflex.models import User, Withdrawal,generate_unique_code, UserPlan, Investment, Commission, InvestmentPlan, Deposit
import os
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.login'))


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(phone=form.phone.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))  # redireciona admin
            else:
                return redirect(url_for('main.dashboard'))   # redireciona usuário comum
        flash('Credenciais inválidas.', 'danger')
    return render_template('login.html', form=form)



@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    # Captura o código de convite da URL (se houver) e pré-preenche o campo
    ref_code = request.args.get('ref')
    if ref_code and not form.referred_by.data:
        form.referred_by.data = ref_code

    if form.validate_on_submit():
        invite_code = generate_unique_code()
        referred_by = form.referred_by.data.strip() if form.referred_by.data else None

        hashed_password = generate_password_hash(form.password.data)
        user = User(
            phone=form.phone.data,
            password=hashed_password,
            invite_code=invite_code,
            referred_by=referred_by
        )
        db.session.add(user)
        db.session.commit()

        flash('Registro realizado com sucesso. Faça login.')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    user = current_user
    deposits = Deposit.query.filter_by(user_id=user.id).order_by(Deposit.timestamp.desc()).all()
    planos = InvestmentPlan.query.filter_by(ativo=True).order_by(InvestmentPlan.valor.asc()).all()
    return render_template('dashboard.html', planos=planos, deposits=deposits, user=user)

@main.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    form = WithdrawalForm()

    if form.validate_on_submit():
        # Verificação de plano ativo
        if not current_user.has_active_plan():
            flash('Você precisa ativar um plano antes de sacar.', 'warning')
            return redirect(url_for('main.withdraw'))

        # Verificação se já sacou hoje
        if current_user.has_withdrawn_today():
            flash('Você já fez um saque hoje. Tente novamente amanhã.', 'info')
            return redirect(url_for('main.withdraw'))

        # Verificação de dados bancários
        if not current_user.bank or not current_user.iban or not current_user.iban_owner:
            flash('Complete seus dados bancários no perfil antes de solicitar o saque.', 'warning')
            return redirect(url_for('main.profile'))  # redireciona para preencher dados

        # Verificar se tem saque pendente
        if current_user.has_pending_withdrawal():
            flash('Você já possui um saque em andamento.', 'warning')
            return redirect(url_for('main.withdraw'))

        # Verifica valor mínimo
        if form.amount.data < 2000:
            flash('O valor mínimo de saque é 2000 AOA.', 'danger')
            return redirect(url_for('main.withdraw'))

        # Verifica saldo
        if current_user.balance < form.amount.data:
            flash('Saldo insuficiente.', 'danger')
            return redirect(url_for('main.withdraw'))

        # Criar solicitação de saque
        new_withdrawal = Withdrawal(
            user_id=current_user.id,
            amount=form.amount.data,
            bank=current_user.bank,
            iban=current_user.iban,
            status='Pendente'
        )
        db.session.add(new_withdrawal)
        current_user.balance -= form.amount.data
        db.session.commit()

        flash('Saque solicitado com sucesso. Aguarde aprovação.', 'success')
        return redirect(url_for('main.wallet'))

    return render_template('withdraw.html', form=form)

@main.route('/referrals')
@login_required
def referrals():
    # Referidos por nível
    nivel1 = current_user.get_referrals(level=1)
    nivel2 = current_user.get_referrals(level=2)
    nivel3 = current_user.get_referrals(level=3)

    # Comissões por nível
    nivel1_total = db.session.query(db.func.sum(Commission.amount)).filter_by(user_id=current_user.id, level=1).scalar() or 0.0
    nivel2_total = db.session.query(db.func.sum(Commission.amount)).filter_by(user_id=current_user.id, level=2).scalar() or 0.0
    nivel3_total = db.session.query(db.func.sum(Commission.amount)).filter_by(user_id=current_user.id, level=3).scalar() or 0.0

    comissao_total = nivel1_total + nivel2_total + nivel3_total

    return render_template(
        'referrals.html',
        nivel1=nivel1,
        nivel2=nivel2,
        nivel3=nivel3,
        nivel1_total=nivel1_total,
        nivel2_total=nivel2_total,
        nivel3_total=nivel3_total,
        comissao_total=comissao_total
    )

@main.route('/wallet')
@login_required
def wallet():
    user = current_user

    # Total investido pelo usuário (somando todos os planos ativos dele)
    total_investido = db.session.query(db.func.sum(UserPlan.investimento))\
        .filter_by(user_id=user.id, ativo=True).scalar() or 0.0

    # Lucro acumulado até agora (usando a property `profit`)
    planos_usuario = UserPlan.query.filter_by(user_id=user.id, ativo=True).all()
    total_lucro = sum([p.profit for p in planos_usuario])

    # Total já recebido (somando `recebido` dos planos)
    total_recebido = sum([p.recebido for p in planos_usuario])

    # Total já sacado
    total_sacado = db.session.query(db.func.sum(Withdrawal.amount))\
        .filter_by(user_id=user.id, status="Aprovado").scalar() or 0.0

    # Saldo atual do usuário (campo balance do User)
    saldo_atual = user.balance

    # Depósitos pendentes
    pendentes = Deposit.query.filter_by(user_id=user.id, status="Pendente").all()

    return render_template(
        "wallet.html",
        total_investido=total_investido,
        total_lucro=total_lucro,
        total_recebido=total_recebido,
        total_sacado=total_sacado,
        saldo_atual=saldo_atual,
        pendentes=pendentes
    )


@main.route('/history')
@login_required
def history():
    investments = Investment.query.filter_by(user_id=current_user.id).order_by(Investment.timestamp.desc()).all()
    withdrawals = Withdrawal.query.filter_by(user_id=current_user.id).order_by(Withdrawal.timestamp.desc()).all()
    commissions = Commission.query.filter_by(user_id=current_user.id).order_by(Commission.timestamp.desc()).all()
    active_plans = UserPlan.query.filter_by(user_id=current_user.id, ativo=True).order_by(UserPlan.criado_em.desc()).all()
    deposits = Deposit.query.filter_by(user_id=current_user.id).order_by(Deposit.timestamp.desc()).all()
    return render_template("history.html",
        investments=investments,
        withdrawals=withdrawals,
        commissions=commissions,
        active_plans=active_plans,
        deposits=deposits
    )



@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.bank = form.bank.data
        current_user.iban = form.iban.data
        current_user.iban_owner = form.iban_owner.data
        db.session.commit()
        flash('Informações atualizadas com sucesso!', 'success')
        return redirect(url_for('main.withdraw'))
    return render_template('profile.html', form=form)


@main.route('/depositar', methods=['GET', 'POST'])
@login_required
def depositar():
    form = DepositForm()

    if form.validate_on_submit():
        valor = form.amount.data  # ajustar aqui para amount
        comprovativo = form.proof.data  # seu campo chama proof, não comprovativo

        filename = secure_filename(comprovativo.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/proofs')
        upload_path = os.path.join(current_app.root_path, upload_folder)

        # Garantir que a pasta existe
        os.makedirs(upload_path, exist_ok=True)

        # Salvar arquivo
        comprovativo.save(os.path.join(upload_path, filename))

        # Salvar no banco
        novo_deposito = Deposit(
            user_id=current_user.id,
            amount=float(valor),
            proof=filename,
            status='Pendente',
            timestamp=datetime.utcnow()
        )
        db.session.add(novo_deposito)
        db.session.commit()

        flash("✅ Depósito enviado para aprovação!", "success")
        return redirect(url_for('main.dashboard'))

    planos = InvestmentPlan.query.all()
    return render_template('deposit.html', form=form, planos=planos)





