KAS_FILE ?= kas/kas-poky-jetson.yml

.PHONY: build menu shell clean

all: shell

# Build the image defined in the KAS_FILE
build:
	kas build $(KAS_FILE)

# Launch the KAS menu for the configuration in KAS_FILE
menu:
	kas menu $(KAS_FILE)

# Enter the KAS shell environment for the configuration in KAS_FILE
shell:
	kas shell $(KAS_FILE)

# Clean the build output
# Note: This is a common Yocto clean target, adjust if your kas setup has a specific clean command
clean:
	rm -rf build/tmp # Adjust this path if your TMPDIR is different
	rm -rf build/sstate-cache # Adjust if your SSTATE_DIR is different