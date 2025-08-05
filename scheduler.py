from cashflex import create_app
from apscheduler.schedulers.background import BackgroundScheduler
from jobs import distribuir_rendimentos

app = create_app()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.app_context().push() or distribuir_rendimentos(), 'interval', hours=24)
    scheduler.start()

if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True)
