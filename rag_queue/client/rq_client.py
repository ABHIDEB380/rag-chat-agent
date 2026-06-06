from redis import Redis
from rq import Queue



# Point this to your Valkey server instance
valkey_conn = Redis(host='localhost', port=6444)

# RQ will seamlessly push jobs to Valkey data structures
queue = Queue(connection=valkey_conn)
