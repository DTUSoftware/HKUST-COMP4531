LOCAL_IP=$(hostname -I | awk '{print $1}')
TOKEN=""
echo url="https://www.duckdns.org/update?domains=hkust-iot&token=${TOKEN}&ip=${LOCAL_IP}" | curl -k -o ~/duckdns/duck.log -K -
