FROM python:3.11-slim

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir torch==2.12.0 --index-url https://download.pytorch.org/whl/cpu

# 4. Install the rest of your LangChain & FastAPI requirements
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/

COPY . .

RUN fastapi dev

EXPOSE 8000



