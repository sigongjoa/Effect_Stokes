FROM lscr.io/linuxserver/blender:latest

# Set a working directory for scripts and outputs
WORKDIR /workspace

# The linuxserver/blender image already sets up Blender in PATH and handles entrypoint.
# We just need to ensure our scripts can be run.

# Copy any necessary scripts or configurations if needed
# COPY . /app

# No ENTRYPOINT needed here, as the base image handles it for Blender.
# Our Python scripts will call Blender directly.