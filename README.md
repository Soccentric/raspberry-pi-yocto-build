# Raspberry Pi Yocto Build

This repository contains scripts and configuration files to build Yocto-based Linux images for Raspberry Pi devices.

## Overview

This project provides an automated build system for creating:
- Custom Linux system images for Raspberry Pi
- Software Development Kit (SDK)
- Extensible Software Development Kit (eSDK)

The build process is containerized using Docker to ensure consistency across development environments.

## Prerequisites

- Git
- Docker
- Make
- Bash shell

## Repository Structure

```
raspberry-pi-yocto-build/
├── docker/             # Docker configuration files
├── full_build.sh       # Main build script
├── copy_sdk.sh         # Helper script to copy SDK to docker
└── Makefile            # Build automation
```

## Build Process

The build process consists of these key steps:

1. Building the Docker image for the system build environment
2. Building the system images for Raspberry Pi
3. Building the SDK (Software Development Kit)
4. Building the eSDK (Extensible Software Development Kit)
5. Copying SDK and eSDK to the Docker container
6. Building SDK and eSDK within the Docker container

## Usage

### Full Automated Build

To perform a complete build including system images, SDK, and eSDK:

```bash
./full_build.sh
```

This script provides detailed progress information and timing statistics for each build step.

### Individual Build Steps

You can also perform individual build steps:

```bash
# Build only the docker image
cd docker && make image

# Build only the system image
make build

# Build only the SDK
make sdk

# Build only the eSDK
make esdk
```

## Build Output

After a successful build, you'll find:
- System images for Raspberry Pi
- SDK installer package
- eSDK installer package

## Troubleshooting

If the build process fails:
1. Check the error messages in the console output
2. Verify your Docker installation is working correctly
3. Ensure you have sufficient disk space and resources for the build

## Development

This project must be run from within its Git repository. The build script automatically detects the repository root and uses it as the working directory.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome and encouraged!

### How to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

Please ensure your code follows the existing style conventions and includes appropriate tests.

### Code of Conduct

Please be respectful and inclusive when contributing to this project.
