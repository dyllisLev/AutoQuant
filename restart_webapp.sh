#!/bin/bash
pkill -9 -f app_new.py
sleep 2
source /opt/AutoQuant/venv/bin/activate
cd /opt/AutoQuant/webapp
nohup python3 app_new.py > /tmp/webapp.log 2>&1 &
sleep 5
echo "서버 재시작 완료"
echo "접속 URL: http://localhost:5000"
