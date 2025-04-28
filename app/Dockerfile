# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt from project root
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the app directory contents
COPY app/ .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run uvicorn server when the container launches
# Use 0.0.0.0 to allow connections from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]