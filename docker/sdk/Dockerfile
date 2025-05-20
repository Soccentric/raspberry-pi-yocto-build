FROM ubuntu:20.04

# Install essential packages for Raspberry Pi development
RUN DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
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
    && apt-get clean 

# Install Yocto Project dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    gawk \
    wget \
    git-core \
    diffstat \
    unzip \
    texinfo \
    gcc-multilib \
    build-essential \
    chrpath \
    socat \
    cpio \
    python3-pip \
    python3-pexpect \
    xz-utils \
    debianutils \
    iputils-ping \
    python3-git \
    python3-jinja2 \
    libsdl1.2-dev \
    python3-subunit \
    mesa-common-dev \
    zstd \
    liblz4-tool \
    file \
    locales \
    && apt-get clean

RUN pip3 install kas

# Set up working directory
WORKDIR /work

# Set environment variables
ENV PYTHONPATH=/workspace:$PYTHONPATH

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create a non-root user
RUN useradd -m jetson && \
    chown -R jetson:jetson /work

# Default command
CMD ["/bin/bash"]
