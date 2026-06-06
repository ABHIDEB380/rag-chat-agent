from .server import app
import uvicorn

def main():
    uvicorn.run(app= app, port=8000, host="localhost")

main()
# To run an uvicorn, the command is python -m rag_queue.main from the PS C:\Users\adebnath\OneDrive - Aptean-online\Learning\Pyhton\RAG path
# where -m represents the module.