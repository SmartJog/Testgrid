#!/bin/sh


PIDFILE=/var/run/tgc.pid
DAEMON=/usr/local/sbin/tgc
ARGV="--host 0.0.0.0 --port 8080"
UID=tgc

status() {
    if start-stop-daemon --status --pidfile $PIDFILE; then
        echo "service is running" >&2
    else
        echo "service is not running" >&2
    fi
}

start() {
    start-stop-daemon\
    --start\
    --pidfile $PIDFILE\
    --make-pidfile\
    --chuid $UID\
    --background\
    --exec $DAEMON -- $ARGV
}

stop() {
    start-stop-daemon --stop --pidfile $PIDFILE
}

case "$1" in
    status)
        status
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
    *)
echo "Usage: $0 {status|start|stop|restart}"
esac