from .app import create_app
from apscheduler.schedulers.background import BackgroundScheduler
from .jobs import distribuir_rendimentos


# Cria o app
app = create_app()

# Garante que os jobs rodem com o contexto da app
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.app_context().push() or distribuir_rendimentos(), 'interval', hours=24)
    scheduler.start()

# Se for executado diretamente
if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True)


