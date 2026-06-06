import sys
import os

# Ensure the project root (RAG/) is on sys.path so RQ can reimport
# rag_queue.queue.worker.process_query when executing jobs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from redis import Redis
from rq import Queue, SimpleWorker

# Connect to your Valkey server
valkey_conn = Redis(host='localhost', port=6444, protocol=2)

if __name__ == '__main__':
    # Define the queues you want this worker to listen to
    queues = Queue(name="default", connection=valkey_conn)

    # Use SimpleWorker to bypass os.fork()
    worker = SimpleWorker([queues], connection=valkey_conn)
    worker.work()
