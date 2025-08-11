import time
from datetime import datetime, date
import pytz
from cashflex import create_app, db
from cashflex.models import JobLog
from jobs import distribuir_rendimentos

app = create_app()
LUANDA_TZ = pytz.timezone("Africa/Luanda")

def ja_executou_hoje(job_name):
    hoje = date.today()
    return JobLog.query.filter_by(job_name=job_name, run_date=hoje).first() is not None

def registrar_execucao(job_name):
    hoje = date.today()
    log = JobLog(job_name=job_name, run_date=hoje)
    db.session.add(log)
    db.session.commit()

def loop_worker():
    with app.app_context():
        while True:
            agora = datetime.now(LUANDA_TZ)
            if agora.hour == 0 and agora.minute == 0 and not ja_executou_hoje("distribuir_rendimentos"):
                print(f"[{agora}] 🚀 Executando distribuição de rendimentos...")
                try:
                    distribuir_rendimentos()
                    registrar_execucao("distribuir_rendimentos")
                    print(f"[{agora}] ✅ Rendimento distribuído com sucesso.")
                except Exception as e:
                    print(f"[{agora}] ❌ Erro ao distribuir rendimentos: {e}")
                time.sleep(60)
            time.sleep(20)

if __name__ == "__main__":
    print("📅 Worker iniciado. Aguardando meia-noite para execução...")
    loop_worker()