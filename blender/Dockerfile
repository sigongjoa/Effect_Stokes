# Blender Dockerfile
# Defines an environment capable of running Blender for headless rendering.

# Start from a base image with NVIDIA OpenGL drivers
FROM nvidia/opengl:1.2-glvnd-runtime-ubuntu22.04

# Set environment variables to non-interactively install packages
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for Blender
# - wget and xz-utils for downloading and extracting Blender
# - libx11-6, libxxf86vm1, libxrender1, libxi6, libgl1 for rendering
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libx11-6 \
    libxxf86vm1 \
    libxrender1 \
    libxi6 \
    libgl1 \
    libsm6 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxinerama1 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    libxv1 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xkb1 \
    && rm -rf /var/lib/apt/lists/*

# Set Blender version and download URL
ENV BLENDER_VERSION=4.0.2
ENV BLENDER_URL=https://download.blender.org/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz

# Download and extract Blender
WORKDIR /usr/local
RUN wget --tries=5 --waitretry=5 -O blender.tar.xz ${BLENDER_URL} && \
    tar -xf blender.tar.xz && \
    rm blender.tar.xz && \
    # Rename for easier access
    mv blender-${BLENDER_VERSION}-linux-x64 blender

# Add Blender to the PATH
ENV PATH="/usr/local/blender:${PATH}"

# Set a working directory for scripts and outputs
WORKDIR /workspace

# Set Blender as the entrypoint. 
# This allows running the container with blender commands directly.
# e.g., docker run blender_runner --background --python my_script.py
ENTRYPOINT ["blender"]