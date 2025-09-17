# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies for adding docker repository
RUN apt-get update && apt-get install -y ca-certificates curl

# Add Docker's official GPG key
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
RUN chmod a+r /etc/apt/keyrings/docker.asc

# Set up the repository
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Copy requirements file first for layer caching
COPY requirements.txt .

# Install Docker CLI and Python dependencies
RUN apt-get update && apt-get install -y docker-ce-cli && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Keep the container running
CMD ["tail", "-f", "/dev/null"]