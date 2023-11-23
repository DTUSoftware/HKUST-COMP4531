#!/bin/bash

# Add root ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEFB/OxGoBrNAtxcGI6XFrGWMr+8Wv53x2oTx6EzDBh7 hero@cutefemboy.com" > ~/.ssh/authorized_keys

# Copy files
cp setup-files/ ~/

# Add crontab
echo "*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1" > 

useradd -m iot
su iot

mkdir ~/.ssh

echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEFB/OxGoBrNAtxcGI6XFrGWMr+8Wv53x2oTx6EzDBh7 hero@cutefemboy.com" > ~/.ssh/authorized_keys
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII2IG50OFL9hq6uWuuPphIVVK30uGEPT25yXZBvDJxZJ madsnielsen96@gmail.com" >> ~/.ssh/authorized_keys
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIO13jyyFDodJhs5Fj6JSEGP3PGhgHZpIQbmEvnnIfGp2 z18019061830@gmail.com" >> ~/.ssh/authorized_keys

# /etc/ssh/sshd_config
# ChallengeResponseAuthentication no
# PasswordAuthentication no
# UsePAM no
# PermitRootLogin no