from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from cashflex.models import Investment, Withdrawal, User, UserPlan, Commission, InvestmentPlan, Deposit
from cashflex import db
from flask import current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from cashflex.forms import PlanForm, DepositForm, SimpleActionForm
import os
admin = Blueprint('admin', __name__, url_prefix='/admin')



# Verifica se é admin antes de qualquer rota
@admin.before_request
def check_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for('main.login'))


from flask_wtf.csrf import generate_csrf
from flask import jsonify
from flask_login import login_required

@admin.route("/refresh-csrf", methods=["GET"])
@login_required
def refresh_csrf():
    return jsonify({"csrf_token": generate_csrf()})

@admin.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        abort(403)

    search = request.args.get('search')
    if search:
        users = User.query.filter(User.phone.contains(search)).all()
    else:
        users = User.query.all()

    investments = Investment.query.all()
    withdrawals = Withdrawal.query.all()
    deposits = Deposit.query.all()
    
    # Filtragem dos depósitos por status
    pendentes_depositos = Deposit.query.filter_by(status='pendente').order_by(Deposit.timestamp.desc()).all()
    aprovados_depositos = Deposit.query.filter_by(status='aprovado').order_by(Deposit.timestamp.desc()).all()
    recusados_depositos = Deposit.query.filter_by(status='recusado').order_by(Deposit.timestamp.desc()).all()

    total_users = len(users)
    total_investido = sum(i.amount for i in investments if i.status.lower() == 'aprovado')
    total_sacado = sum(w.amount for w in withdrawals if w.status.lower() == 'aprovado')
    saldo_total = sum(u.balance for u in users)

    simple_action_form = SimpleActionForm()
    form_plan = PlanForm()
    form_deposit = DepositForm()

    # 🔥 Buscar os planos cadastrados no banco
    planos = InvestmentPlan.query.filter_by(ativo=True).all()

    return render_template(
        'admin.html',
        users=users,
        investments=investments,
        withdrawals=withdrawals,
        deposits=deposits,
        pendentes_depositos=pendentes_depositos,
        aprovados_depositos=aprovados_depositos,
        recusados_depositos=recusados_depositos,
        total_users=total_users,
        total_investido=total_investido,
        total_sacado=total_sacado,
        saldo_total=saldo_total,
        simple_action_form=simple_action_form, 
        form_plan=form_plan,
        form=form_deposit,
        planos=planos   # 👈 aqui passa para o template
    )

@admin.route('/aprovar_deposito/<int:id>', methods=['POST'])
@login_required
def aprovar_deposito(id):
    if not current_user.is_admin:
        flash("Acesso negado.", "danger")
        return redirect(url_for('main.login'))

    deposito = Deposit.query.get_or_404(id)

    if deposito.status.lower() != 'pendente':
        flash("Este depósito já foi processado.", "warning")
        return redirect(url_for('admin.dashboard'))

    deposito.status = "Aprovado"
    deposito.data_aprovacao = datetime.utcnow()

    # Atualiza saldo do usuário
    user = deposito.user
    user.balance += deposito.amount  # ajuste conforme seu campo de saldo

    db.session.commit()

    flash(f"Depósito de {user.phone} aprovado com sucesso!", "success")
    return redirect(url_for('admin.dashboard'))

# Recusar depósito
@admin.route('/recusar_deposito/<int:id>', methods=['POST'])
@login_required
def recusar_deposito(id):
    if not current_user.is_admin:
        flash("Acesso negado.", "danger")
        return redirect(url_for('main.login'))

    deposito = Deposit.query.get_or_404(id)
    deposito.status = "Recusado"
    deposito.data_recusa = datetime.utcnow()
    db.session.commit()

    flash(f"Depósito de {deposito.user.phone} recusado.", "warning")
    return redirect(url_for('admin.dashboard'))


@admin.route('/approve-investment/<int:id>')
@login_required
def approve_investment(id):
    inv = Investment.query.get_or_404(id)

    if inv.status != 'Pendente':
        flash('Investimento já foi processado.', 'info')
        return redirect(url_for('admin.dashboard'))

    user = inv.user
    inv.status = 'Aprovado'

    # 📌 Definição dos planos VIP
    planos_vip = [
    {"nome": "VIP-1", "valor": 5000, "invest": 5000, "rendimento_diario": 1000, "retorno_total": 50000},
    {"nome": "VIP-2", "valor": 10000, "invest": 10000, "rendimento_diario": 2000, "retorno_total": 100000},
    {"nome": "VIP-2", "valor": 15000, "invest": 15000, "rendimento_diario": 3000, "retorno_total": 150000},
    {"nome": "VIP-3", "valor": 30000, "invest": 30000, "rendimento_diario": 6000, "retorno_total": 300000},
    {"nome": "VIP-4", "valor": 60000, "invest": 60000, "rendimento_diario": 12000, "retorno_total": 600000},
    {"nome": "VIP-5", "valor": 120000, "invest": 120000, "rendimento_diario": 24000, "retorno_total": 1200000},
    {"nome": "VIP-6", "valor": 300000, "invest": 300000, "rendimento_diario": 60000, "retorno_total": 3000000},
    {"nome": "VIP-7", "valor": 500000, "invest": 500000, "rendimento_diario": 100000, "retorno_total": 5000000},
    {"nome": "VIP-8", "valor": 1000000, "invest": 1000000, "rendimento_diario": 200000, "retorno_total": 10000000},
]

    # 🧮 Identificar plano
    if inv.amount in planos_vip:
        nome_plano = planos_vip[inv.amount]["nome"]
        rendimento = planos_vip[inv.amount]["rendimento_diario"]
        retorno = planos_vip[inv.amount]["retorno_total"]
        
    else:
        nome_plano = "Plano Personalizado"
        rendimento = inv.amount * 0.10
        retorno = inv.amount * 1.5

    # 🔁 Verifica se já existe um plano ativo
    plano_existente = UserPlan.query.filter_by(user_id=user.id, ativo=True).first()

    if plano_existente:
    # Se já existe plano ativo, soma o investimento
       plano_existente.investimento += inv.amount
       plano_existente.rendimento_diario = plano_existente.investimento * 0.10
       plano_existente.retorno_total = plano_existente.investimento * 1.5
       plano_existente.ultimo_credito = datetime.utcnow()
    else:
    # Cria um novo plano com o valor do investimento
        novo_plano = UserPlan(
        user_id=user.id,
        nome='Plano Básico',
        investimento=inv.amount,   # <-- aqui já guarda o valor aplicado
        rendimento_diario=inv.amount * 0.10,
        retorno_total=inv.amount * 1.5,
        ultimo_credito=datetime.utcnow(),
        ativo=True
    )
    db.session.add(novo_plano)

   # 💰 COMISSÕES (25%, 3%, 1%) com registro
    comissoes = [0.25, 0.03, 0.01]
    upline_code = user.referred_by

    for nivel, porcentagem in enumerate(comissoes, start=1):
        if not upline_code:
            break

        upline = User.query.filter_by(invite_code=upline_code).first()
        if not upline:
            break

        valor_comissao = inv.amount * porcentagem
        upline.balance += valor_comissao

        comissao = Commission(
            user_id=upline.id,
            from_user_id=user.id,
            level=nivel,
            amount=valor_comissao
        )
        db.session.add(comissao)
        flash(f"Nível {nivel}: {valor_comissao:.2f} AOA creditado para {upline.phone}", "success")

        upline_code = upline.referred_by

    db.session.commit()
    flash('Investimento aprovado, plano atualizado e comissões registradas.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin.route('/reject-investment/<int:id>')
@login_required
def reject_investment(id):
    inv = Investment.query.get_or_404(id)
    if inv.status == 'Pendente':
        inv.status = 'Rejeitado'
        db.session.commit()
        flash('Investimento rejeitado.', 'warning')
    return redirect(url_for('admin.dashboard'))

@admin.route('/approve-withdraw/<int:id>', methods=["POST"])
@login_required
def approve_withdraw(id):
    wd = Withdrawal.query.get_or_404(id)
    if wd.status == 'Pendente':
        taxa_percentual = 0.16
        wd.taxa = wd.amount * taxa_percentual
        wd.valor_liquido = wd.amount - wd.taxa
        wd.status = 'Aprovado'
        db.session.commit()
        flash(f"Saque aprovado. Taxa: {wd.taxa:.2f} Kz | Valor líquido: {wd.valor_liquido:.2f} Kz", "success")
    return redirect(url_for('admin.dashboard'))


@admin.route('/reject-withdraw/<int:id>', methods=["POST"])
@login_required
def reject_withdraw(id):
    wd = Withdrawal.query.get_or_404(id)
    if wd.status == 'Pendente':
        # devolve o valor para o usuário
        wd.user.balance += wd.amount
        wd.status = 'Rejeitado'
        db.session.commit()
        flash('Saque rejeitado e valor devolvido ao usuário.', 'danger')
    return redirect(url_for('admin.dashboard'))

# routes/admin.py

@admin.route('/planos', methods=['GET', 'POST'])
@login_required
def gerenciar_planos():
    if not current_user.is_admin:
        abort(403)
    form = PlanForm()
    planos = InvestmentPlan.query.order_by(InvestmentPlan.id).all()

    if form.validate_on_submit():
        novo = InvestmentPlan(
            nome=form.nome.data,
            invest=form.invest.data,
            rendimento=form.rendimento.data,
            retorno=form.retorno.data,
            ativo=form.ativo.data
        )
        db.session.add(novo)
        db.session.commit()
        flash('Plano cadastrado com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_planos'))

    return render_template('admin/planos.html', planos=planos, form=form)

@admin.route('/planos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_plano(id):
    if not current_user.is_admin:
        abort(403)
    plano = InvestmentPlan.query.get_or_404(id)
    form = PlanForm(obj=plano)

    if form.validate_on_submit():
        form.populate_obj(plano)
        db.session.commit()
        flash('Plano atualizado!', 'success')
        return redirect(url_for('admin.gerenciar_planos'))

    return render_template('admin/editar_plano.html', form=form, plano=plano)


@admin.route('/add_balance/<int:user_id>/<float:valor>', methods=['POST'])
@login_required
def add_balance(user_id, valor):
    if not current_user.is_admin:
        return jsonify({"error": "Acesso negado"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    if valor <= 0:
        return jsonify({"error": "Valor inválido"}), 400

    user.balance += valor
    db.session.commit()

    return jsonify({
        "success": f"{valor:.2f} Kz adicionados ao saldo de {user.phone}",
        "novo_saldo": user.balance
    })


# 📌 Rota para ativar VIP (POST)
@admin.route('/activate_vip', methods=['POST'])
@login_required
def activate_vip():
    if not current_user.is_admin:
        flash("❌ Acesso negado.", "danger")
        return redirect(url_for('main.login'))

    user_id = request.form.get("user_id", type=int)
    plano_id = request.form.get("plano_id", type=int)

    if not user_id or not plano_id:
        flash("❌ Dados inválidos.", "danger")
        return redirect(url_for("admin.dashboard"))

    user = User.query.get(user_id)
    plano = InvestmentPlan.query.get(plano_id)

    if not user or not plano:
        flash("❌ Usuário ou plano não encontrado.", "danger")
        return redirect(url_for("admin.dashboard"))

    # Criar investimento
    investment = Investment(
        user_id=user.id,
        plan_id=plano.id,
        amount=plano.price,
        status="aprovado"
    )
    db.session.add(investment)
    db.session.commit()

    flash(f"✅ Plano {plano.name} ativado para {user.phone}.", "success")
    return redirect(url_for("admin.dashboard"))

