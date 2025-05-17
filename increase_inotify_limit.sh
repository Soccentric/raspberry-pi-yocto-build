#!/bin/bash

echo "Checking current inotify limits..."
echo "Current limits:"
echo "* fs.inotify.max_user_watches: $(cat /proc/sys/fs/inotify/max_user_watches)"
echo "* fs.inotify.max_user_instances: $(cat /proc/sys/fs/inotify/max_user_instances)"

# Increase the limit temporarily (until reboot)
echo "Increasing limits temporarily..."
sudo sysctl -w fs.inotify.max_user_watches=524288
sudo sysctl -w fs.inotify.max_user_instances=512

echo "New limits:"
echo "* fs.inotify.max_user_watches: $(cat /proc/sys/fs/inotify/max_user_watches)"
echo "* fs.inotify.max_user_instances: $(cat /proc/sys/fs/inotify/max_user_instances)"

# Make the change permanent
echo "Making changes permanent..."
if ! grep -q "fs.inotify.max_user_watches" /etc/sysctl.conf; then
    echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf > /dev/null
fi

if ! grep -q "fs.inotify.max_user_instances" /etc/sysctl.conf; then
    echo "fs.inotify.max_user_instances=512" | sudo tee -a /etc/sysctl.conf > /dev/null
fi

echo "Setup complete. The limits have been increased temporarily and will persist after reboot."
echo "You can now run the Jetson Build Manager application."
