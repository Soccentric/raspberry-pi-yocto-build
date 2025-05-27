FROM ubuntu:20.04

# Prevent interactive prompts during package installation
ARG DEBIAN_FRONTEND=noninteractive

# Install essential build packages
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    build-essential \
    chrpath \
    diffstat \
    gawk \
    texinfo \
    wget \
    curl \
    unzip \
    locales \
    cpio \
    file \
    xz-utils \
    sudo \
    lz4 \
    zstd \
    gcc-multilib \
    g++-multilib \
    libssl-dev \
    vim \
    tmux \
    nano \
    bc \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Install kas
RUN pip3 install kas

# Create build user (to avoid running as root)
RUN useradd -ms /bin/bash build && \
    echo "build ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/build && \
    chmod 0440 /etc/sudoers.d/build

# Create work directory and change ownership
RUN mkdir -p /work && chown build:build /work

# Switch to build user
USER build
WORKDIR /work

# Set default command
CMD ["/bin/bash"]
