FROM ubuntu:24.04

# Install essential packages for Raspberry Pi development
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-dev \
    python3-pip \
    wget \
    nano \
    libhdf5-dev \
    libatlas-base-dev \
    libjpeg-dev \
    libpng-dev \
    curl \
    ssh \
    rsync \
    python3-gpiozero \
    python3-rpi.gpio \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*



# Set up working directory
WORKDIR /workspace

# Set environment variables
ENV PYTHONPATH=/workspace:$PYTHONPATH

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create a non-root user
RUN useradd -m pi && \
    chown -R pi:pi /workspace

# Default command
CMD ["/bin/bash"]
