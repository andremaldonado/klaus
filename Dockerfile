# Use official Python runtime as a parent image
FROM python:3.13-slim

# Set working directory
WORKDIR /app/src/klaus

# Copy requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src/klaus/ .

# Expose port for Functions Framework
ENV PORT=8080
EXPOSE 8080

# Run the Functions Framework to serve the 'create_app' function
ENTRYPOINT ["functions-framework", "--target=create_app", "--port=8080"]