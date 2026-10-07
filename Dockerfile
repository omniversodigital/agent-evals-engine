FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["compare", "--dataset", "data/golden_dataset.json", "--prompt-a", "data/prompt_v1.txt", "--prompt-b", "data/prompt_v2.txt"]
