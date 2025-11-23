FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy solver code
COPY solver_core.py app.py ./

# Expose port
EXPOSE 7070

# Run solver service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7070"]
