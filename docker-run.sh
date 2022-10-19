#!/bin/sh
set -eu

docker run \
    -e 'TARGETS=192.168.0.11,192.168.0.14' \
    -e 'BROKER=192.168.0.2' \
    -e 'POLLING_PERIOD=5' \
    -e 'LOG_LEVEL=DEBUG' \
    --rm \
    --name ping-mqtt \
    mathieuclement/ping-mqtt:latest
