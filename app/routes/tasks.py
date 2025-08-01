from datetime import datetime, date
from app import create_app, db
from app.models import UserPlan

app = create_app()

with app.app_context():
    planos = UserPlan.query.filter_by(ativo=True).all()
    hoje = date.today()
    creditados = 0

    for plano in planos:
        if plano.ultimo_credito and plano.ultimo_credito.date() == hoje:
            continue

        rendimento = plano.investimento * 0.20
        plano.user.balance += rendimento
        plano.ultimo_credito = datetime.utcnow()
        creditados += 1

    db.session.commit()
    print(f"✅ {creditados} planos creditados com sucesso!")

