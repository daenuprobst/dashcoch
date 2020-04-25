import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
