# Use a modern, secure, and supported version of Python
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy all local code (app.py, requirements.txt, templates/, etc.) to the container
COPY . .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application using Gunicorn (a production-ready server)
# The PORT environment variable will be provided automatically by Azure App Service
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
