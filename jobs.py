# jobs.py
from datetime import datetime, date
from cashflex import db
from cashflex.models import UserPlan, User

def distribuir_rendimentos():
    hoje = date.today()
    count = 0

    # Busca planos ativos e já traz o usuário junto (JOIN)
    planos = (
        db.session.query(UserPlan, User)
        .join(User, UserPlan.user_id == User.id)
        .filter(UserPlan.ativo == True)
        .all()
    )

    for plano, user in planos:
        # Evita pagar mais de uma vez no mesmo dia
        if plano.ultimo_credito and plano.ultimo_credito.date() == hoje:
            continue

        # Inicializa recebido se for None
        if plano.recebido is None:
            plano.recebido = 0.0

        # Atualiza saldo e registro de plano
        user.balance += plano.rendimento_diario
        plano.recebido += plano.rendimento_diario
        plano.ultimo_credito = datetime.utcnow()

        # Finaliza plano se atingir retorno total
        if plano.recebido >= plano.retorno_total:
            plano.ativo = False
            print(f"Plano ID {plano.id} finalizado para usuário {user.id}")

        count += 1

    db.session.commit()
    print(f"[{datetime.now()}] Rendimento distribuído para {count} planos.")

