from config import celery_app


@celery_app.task()
def something():

    pass
