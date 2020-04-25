import multiprocessing

# workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"

# Keep things clean and neat (and leak-free)
max_requests = 1200
