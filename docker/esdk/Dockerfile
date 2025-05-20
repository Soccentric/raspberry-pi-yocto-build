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

# Generate and set locale
RUN locale-gen en_US.UTF-8 && update-locale LANG=en_US.UTF-8

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

RUN pip3 install kas




# Set up working directory
WORKDIR /work

# Set environment variables
ENV PYTHONPATH=/workspace:$PYTHONPATH

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Accept build arguments for UID and GID
ARG JETSON_UID=1000
ARG JETSON_GID=1000

COPY esdk.sh /tmp/esdk.sh
RUN chmod +x /tmp/esdk.sh

# Create group and user with specified UID/GID
RUN groupadd -g $JETSON_GID jetson || true && \
    useradd -m -u $JETSON_UID -g $JETSON_GID jetson && \
    chown -R jetson:jetson /work

USER jetson



RUN /tmp/esdk.sh

# Default command
CMD ["/bin/bash"]
