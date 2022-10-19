# Ping MQTT

This daemon will ping a device on the network (or on the Internet if your heart desires) and
report the status on an MQTT topic.

It can do so either periodically or when it receives a `ping` command the `/command` MQTT topic,
or both.

## MQTT topics

There are 3 topics per device:

  - `/ping/<host>`: publishes payloads `on` or `off`. It will try pinging for 30 seconds before
    returning an `off` payload, otherwise as soon as one of the pings succeed, the `on` payload
    is sent. The number and duration of pings is not currently modifiable. Feel free to submit
    a PR to make it configurable.
  - `/ping/<host>/command`: you can send the `ping` payload to force an update
  - `/ping/<host>/availability`: publishes `online` when starting the service or `offline`
    when the processes receives a `SIGINT` signal (e.g. by pressing Ctrl-C from the terminal).

## MQTT broker

The broker can be configured through the `BROKER` environment variable, assuming the default
port 1883. Feel free to submit a PR to support TLS and custom ports.

## Polling period

The polling period is configurable through the `POLLING_PERIOD` environment variable, value
is an integer to describe a period in seconds, e.g. `60` will poll hosts one after the other
every minute. Polling is disabled by default, if the variable isn't set or is set to a 
value of `-1`.
