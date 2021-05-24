pid=$(ps -e | pgrep tcpdump)
echo $pid

sudo kill -SIGINT $pid