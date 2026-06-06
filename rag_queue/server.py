from fastapi import FastAPI, HTTPException
from .client.rq_client import queue
from .queue.worker import process_query

app = FastAPI()

@app.get("/")
def root():
    return {"status" : "Fast api is running"}

@app.post("/chat")
def chat(query:str):
    print("query is: ", {query})
    job = queue.enqueue(process_query, query)
    return {"status" : "Enqued the job", "job_id" : job.id }

@app.get("/response")
def get_result(job_id:str):
    job = queue.fetch_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    status = job.get_status(refresh=True)

    if status == "finished":
        return {
            "job_id": job.id,
            "status": status,
            "result": job.return_value(refresh=True),
        }

    if status == "failed":
        return {
            "job_id": job.id,
            "status": status,
            "error": job.exc_info,
        }

    return {
        "job_id": job.id,
        "status": status,
        "result": None,
    }