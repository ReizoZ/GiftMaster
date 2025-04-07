
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt


FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .


ENV PATH=/root/.local/bin:$PATH


RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*


ENV FLASK_RUN_HOST=0.0.0.0
VOLUME /app/Database
CMD python app.py & python bot.py
