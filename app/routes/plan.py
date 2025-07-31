from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models import Investment, UserPlan, Commission, User, InvestmentPlan
from app.forms import InvestForm
from app import db
from datetime import datetime
from werkzeug.utils import secure_filename
import os

plan = Blueprint('plan', __name__)

# 📂 Extensões permitidas para comprovativos
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@plan.route('/invest', methods=['GET', 'POST'])
@login_required
def invest():
    form = InvestForm()

    if form.validate_on_submit():
        valor = form.amount.data

        # ✅ Verificação de valor mínimo
        if valor < 5000:
            flash('O valor mínimo para investir é 5.000 AOA.', 'warning')
            return redirect(url_for('plan.invest'))

        # 📁 Processa comprovativo (se houver)
        filename = None
        if form.proof.data:
            file = form.proof.data
            filename = secure_filename(file.filename)

            if not allowed_file(filename):
                flash('Formato de arquivo não permitido. Envie JPG, PNG ou PDF.', 'danger')
                return redirect(url_for('plan.invest'))

            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        # 🕓 Cria investimento pendente
        investment = Investment(
            user_id=current_user.id,
            amount=valor,
            proof=filename,
            status='Pendente'
        )

        db.session.add(investment)
        db.session.commit()

        flash('Investimento enviado para aprovação. Aguarde validação.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('invest.html', form=form)


@plan.route('/activate-plan/<int:id>')
@login_required
def activate_plan(id):
    inv = Investment.query.get_or_404(id)

    if inv.status != 'Aprovado' or inv.user_id != current_user.id:
        flash('Investimento inválido ou já utilizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    # ⛔ Impede mais de um plano ativo por usuário
    plano_existente = UserPlan.query.filter_by(user_id=current_user.id, ativo=True).first()
    if plano_existente:
        flash('Você já possui um plano ativo.', 'warning')
        return redirect(url_for('main.dashboard'))

    # 🔢 Parâmetros do plano
    rendimento = inv.amount * 0.10
    dias_duracao = 5
    retorno_total = rendimento * dias_duracao

    plano = UserPlan(
        user_id=current_user.id,
        nome="Plano Simples",
        investimento=inv.amount,
        rendimento_diario=rendimento,
        retorno_total=retorno_total,
        ativo=True,
        data_inicio=datetime.utcnow()
    )
    db.session.add(plano)

    # ⛔ Marca investimento como usado
    inv.status = 'Usado'
    db.session.add(inv)

    # 💰 Gera comissões de referência
    gerar_comissoes(current_user, inv.amount)

    db.session.commit()
    flash('Plano ativado com sucesso!', 'success')
    return redirect(url_for('main.dashboard'))


@plan.route('/confirmar_plano/<int:plano_id>')
@login_required
def confirmar_plano(plano_id):
    plano = InvestmentPlan.query.get_or_404(plano_id)

    if plano.ativo is False:
        flash('Este plano está indisponível no momento.', 'warning')
        return redirect(url_for('main.dashboard'))

    valor = plano.valor_minimo

    # 💰 Verifica saldo do usuário
    if current_user.balance < valor:
        flash('Saldo insuficiente para investir neste plano.', 'warning')
        return redirect(url_for('main.dashboard'))

    # ⛔ Impede duplicidade de planos ativos
    ativo = UserPlan.query.filter_by(user_id=current_user.id, ativo=True).first()
    if ativo:
        flash('Você já possui um plano ativo.', 'warning')
        return redirect(url_for('main.dashboard'))

    # ✅ Cria o plano
    novo_plano = UserPlan(
        user_id=current_user.id,
        nome=plano.nome,
        investimento=valor,
        rendimento_diario=plano.rendimento_diario,
        retorno_total=plano.retorno_total,
        ativo=True,
        data_inicio=datetime.utcnow()
    )
    db.session.add(novo_plano)

    # 💸 Debita valor do saldo
    current_user.balance -= valor
    db.session.add(current_user)

    # 💰 Gera comissões diretas
    gerar_comissoes(current_user, valor)

    db.session.commit()
    flash(f'Você adquiriu o plano {plano.nome} com sucesso!', 'success')
    return redirect(url_for('main.dashboard'))


def gerar_comissoes(user, amount):
    """Gera comissões para 3 níveis de uplines"""
    comissoes = [0.25, 0.03, 0.01]
    upline_code = user.referred_by

    for nivel, percentual in enumerate(comissoes, start=1):
        if not upline_code:
            break

        upline = User.query.filter_by(invite_code=upline_code).first()
        if not upline:
            break

        valor = amount * percentual
        com = Commission(
            user_id=upline.id,
            from_user_id=user.id,
            level=nivel,
            amount=valor
        )
        upline.balance += valor
        db.session.add(com)
        db.session.add(upline)

        upline_code = upline.referred_by  # próximo nível



