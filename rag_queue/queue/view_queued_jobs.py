from redis import Redis
from rq import Queue, SimpleWorker

# Connect to your Valkey server (defaults to localhost:6379)
valkey_conn = Redis(host='localhost', port=6444)

# Define the queues you want this worker to listen to
queue = Queue(name="default", connection=valkey_conn)

q = queue.fetch_job(job_id="f96a76cf-f42f-4f87-89e5-d8c823228785")

print(q.return_value)
# queued_jobs = queue.jobs

# # Or get just the job IDs
# # queued_job_ids = queue.job_ids

# # Print out job details
# for job in queued_jobs:
#     print(f"Job ID: {job.id} | Function: {job.func_name}")
# else:
#     print("No jobs avilable")