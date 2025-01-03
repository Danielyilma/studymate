#!/bin/bash

# create and start a virtual environment
python3 -m venv venv
source /home/ubuntu/studymate/venv/bin/activate

pip install -r requirements.txt

python3 manage.py migrate

# deamon service configration
project_service="[Unit]
Description=Studymate Gunicorn Daemon
After=network.target

[Service]
User=root
Group=root
Environment="PATH=/home/ubuntu/studymate/venv/bin"
WorkingDirectory=/home/ubuntu/studymate/
ExecStart=/home/ubuntu/studymate/venv/bin/gunicorn --workers 3 --bind unix:/home/ubuntu/studymate/studymate.sock studymate.wsgi:application

[Install]
WantedBy=multi-user.target
"

echo "$project_service" | sudo tee /etc/systemd/system/gunicorn-studymate.service

sudo systemctl daemon-reload

sudo systemctl start gunicorn-studymate
sudo systemctl enable gunicorn-studymate


# nginx configration

nginx_config="server {
    listen 80;
    server_name 54.160.76.121;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/studymate/studymate.sock;
    }
}
"

echo "$nginx_config" | sudo tee /etc/nginx/sites-available/studymate

sudo ln -s /etc/nginx/sites-available/studymate /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl restart nginx
