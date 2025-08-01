from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from cashflex_app.app import db
from cashflex_app.app.forms import LoginForm, RegisterForm, WithdrawalForm, ProfileForm
from cashflex_app.app.models import User, Withdrawal,generate_unique_code, UserPlan, Investment, Commission, InvestmentPlan

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
    planos = InvestmentPlan.query.filter_by(ativo=True).order_by(InvestmentPlan.valor.asc()).all()
    return render_template('dashboard.html', planos=planos)

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
        if form.amount.data < 1200:
            flash('O valor mínimo de saque é 1.200 AOA.', 'danger')
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
    nivel1 = current_user.get_referrals(level=1)
    nivel2 = current_user.get_referrals(level=2)
    nivel3 = current_user.get_referrals(level=3)

    return render_template(
        'referrals.html',
        nivel1=nivel1,
        nivel2=nivel2,
        nivel3=nivel3
    )

@main.route('/wallet')
@login_required
def wallet():
    total_investido = sum([inv.amount for inv in current_user.investments]) if current_user.investments else 0
    total_lucro = sum([plan.profit for plan in current_user.planos_ativos if plan.ativo]) if current_user.planos_ativos else 0

    return render_template('wallet.html',
                           total_investido=total_investido,
                           total_lucro=total_lucro)

@main.route('/history')
@login_required
def history():
    investments = Investment.query.filter_by(user_id=current_user.id).order_by(Investment.timestamp.desc()).all()
    withdrawals = Withdrawal.query.filter_by(user_id=current_user.id).order_by(Withdrawal.timestamp.desc()).all()
    commissions = Commission.query.filter_by(user_id=current_user.id).order_by(Commission.timestamp.desc()).all()
    active_plans = UserPlan.query.filter_by(user_id=current_user.id, ativo=True).order_by(UserPlan.criado_em.desc()).all()

    return render_template("history.html",
        investments=investments,
        withdrawals=withdrawals,
        commissions=commissions,
        active_plans=active_plans
    )


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.bank = form.bank.data
        current_user.iban = form.iban.data
        current_user.iban_owner = form.iban_owner.data
        current_user.multicaixa = form.multicaixa.data
        db.session.commit()
        flash('Informações atualizadas com sucesso!', 'success')
        return redirect(url_for('main.withdraw'))
    return render_template('profile.html', form=form)



