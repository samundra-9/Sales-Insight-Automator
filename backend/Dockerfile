# Use a Python base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app/backend

# Copy the backend application code
COPY ./app /app/backend/app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

