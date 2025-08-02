
from datetime import datetime, timedelta
from app import db
from app.models import UserPlan, User

def distribuir_rendimentos():
    planos = UserPlan.query.filter_by(ativo=True).all()
    agora = datetime.utcnow()
    count = 0

    for plano in planos:
        if plano.ultima_distribuicao is None or (agora - plano.ultima_distribuicao) >= timedelta(hours=20):
            user = User.query.get(plano.user_id)
            if not user:
                continue

            if plano.recebido is None:
                plano.recebido = 0.0

            user.balance += plano.rendimento_diario
            plano.recebido += plano.rendimento_diario
            plano.ultima_distribuicao = agora

            if plano.recebido >= plano.retorno_total:
                plano.ativo = False

            db.session.add(user)
            db.session.add(plano)
            count += 1

    db.session.commit()
    print(f"[{datetime.now()}] Rendimento distribuído para {count} planos.")


if __name__ == "__main__":
    from app import app
    with app.app_context():
        distribuir_rendimentos()


