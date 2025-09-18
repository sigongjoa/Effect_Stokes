# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Create a non-root user and group with UID/GID 911
RUN groupadd -g 911 appuser && useradd -u 911 -g appuser -m appuser

# Create /workspace and set ownership for appuser
RUN mkdir -p /workspace && chown appuser:appuser /workspace

# Create a group with the host's docker GID (108)
RUN groupadd -g 108 docker_host_group || true
# Add the appuser to this docker_host_group
RUN usermod -a -G docker_host_group appuser

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
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]