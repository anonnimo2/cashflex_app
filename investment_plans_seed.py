from app import create_app, db
from app.models import InvestmentPlan

app = create_app()

planos = [
    {"nome": "VIP-1", "invest": 5000},
    {"nome": "VIP-2", "invest": 15000},
    {"nome": "VIP-3", "invest": 30000},
    {"nome": "VIP-4", "invest": 60000},
    {"nome": "VIP-5", "invest": 120000},
    {"nome": "VIP-6", "invest": 300000},
    {"nome": "VIP-7", "invest": 500000},
    {"nome": "VIP-8", "invest": 1000000},
]

with app.app_context():
    for plano in planos:
        existente = InvestmentPlan.query.filter_by(nome=plano["nome"]).first()
        if existente:
            print(f"Plano {plano['nome']} já existe. Pulando.")
            continue

        invest = plano["invest"]
        rendimento_diario = round(invest * 0.20, 2)
        retorno_total = round(invest * 2.0, 2)

        novo_plano = InvestmentPlan(
            nome=plano["nome"],
            invest=invest,
            rendimento_diario=rendimento_diario,
            retorno_total=retorno_total,
            ativo=True,
            valor=invest  # usado para ordenação se desejar
        )
        db.session.add(novo_plano)

    db.session.commit()
    print("Planos de investimento populados com sucesso.")
