from app.services.celery_tasks import celery

if __name__ == "__main__":
    celery.worker_main(argv=["worker", "--loglevel=info"])