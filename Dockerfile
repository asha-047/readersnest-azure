# --- START OF CHANGES ---
# Use a modern, secure, and supported version of Python
FROM python:3.11-slim
# --- END OF CHANGES ---

# Set the working directory in the container
WORKDIR /app

# Copy the local code to the container
COPY . .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application using Gunicorn
# The PORT environment variable will be provided by Azure App Service
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
