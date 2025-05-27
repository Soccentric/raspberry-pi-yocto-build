FROM ubuntu:22.04

# Set non-interactive frontend to avoid prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

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
    \
    && apt-get clean 

# Install Yocto Project dependencies
RUN apt-get update && apt-get install -y \
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


# Install kas using pip (Python package installer)
RUN pip3 install kas

# Set up working directory
WORKDIR /work

# Copy SDK installer script
COPY esdk.sh /tmp/esdk.sh

# Set environment variables
ENV PYTHONPATH=/workspace:$PYTHONPATH

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create a non-root user with host user ID for permission sync
ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} pi && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -m pi && \
    chown -R pi:pi /work

# Create SDK directory and set permissions
RUN mkdir -p /opt/sdk && \
    chmod +x /tmp/esdk.sh && \
    chown -R pi:pi /opt/sdk /tmp/esdk.sh

# Configure and generate locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Switch to pi user and install SDK
USER pi
RUN /tmp/esdk.sh -y -d /opt/sdk

# Add the SDK environment sourcing to .bashrc
RUN echo 'source /opt/sdk/environment-setup-cortexa76-poky-linux' >> /home/pi/.bashrc

# Default command
CMD ["/bin/bash"]
