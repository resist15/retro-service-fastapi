import multiprocessing

workers = int(multiprocessing.cpu_count() + 1)

worker_class = "uvicorn_worker.UvicornWorker"

bind = "0.0.0.0:8000"

preload_app = True

proc_name = "retro-service"
