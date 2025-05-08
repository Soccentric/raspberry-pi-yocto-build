# Jetson/Raspberry Pi Yocto Build System

A streamlined build system for creating embedded Linux images for Jetson and Raspberry Pi devices using Yocto Project and KAS.

## Features

- Web-based UI for build management using Streamlit
- KAS configuration for simplified Yocto builds
- Support for multiple Raspberry Pi boards
- Integrated build tools with Makefile targets

## Prerequisites

- Linux-based operating system
- Python 3.6+
- Git
- Docker (optional, recommended for isolated builds)
- Required packages for Yocto builds (see [Yocto Project Quick Start](https://docs.yoctoproject.org/brief-yoctoprojectqs/index.html))

## Setup

1. Clone this repository:

```bash
git clone https://github.com/yourusername/jetson.git
cd jetson
```

2. Run the setup script:

```bash
./setup.sh
```

This will create a Python virtual environment and install required dependencies.

## Usage

### Web Interface

Start the web interface:

```bash
./run.sh
```

This will launch a Streamlit web application accessible at http://localhost:8501

### Command Line

You can also use the Makefile directly:

```bash
# Build the default image
make build

# Enter the interactive KAS shell
make shell

# Launch the KAS menu
make menu

# Clean the build artifacts
make clean
```

## Configuration

The default configuration is in `kas/kas-poky-jetson.yml`. You can override variables at build time:

```bash
KAS_MACHINE=raspberrypi4 make build
```

### Available machine configurations:

- raspberrypi
- raspberrypi2
- raspberrypi3
- raspberrypi4
- raspberrypi5
- raspberrypi-cm-4
- raspberrypi-cm-5
- raspberrypi-w
- raspberrypi-w2

## Project Structure

- `app.py` - Streamlit web application
- `Makefile` - Build targets
- `kas/` - KAS configuration files
  - `machines/` - Machine configurations
  - `distros/` - Distribution configurations
  - `images/` - Image configurations
  - `repos/` - Layer repository definitions
- `layers/` - Downloaded Yocto layers
- `build/` - Build output directory

## License

[Insert license information here]
