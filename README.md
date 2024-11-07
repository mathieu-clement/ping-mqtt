# Ping MQTT

This daemon will ping a device on the network (or on the Internet if your heart desires) and
report the status on an MQTT topic.

It can do so either periodically or when it receives a `ping` command on the `/command` MQTT 
topic, or both.

## MQTT topics

There are three topics per device:

  - `/ping/<host>`: publishes payloads `on` or `off`. It will try pinging for 30 seconds before
    returning an `off` payload, otherwise as soon as one of the pings succeed, the `on` payload
    is sent. The number and duration of pings is not currently modifiable. Feel free to submit
    a PR to make it configurable.
  - `/ping/<host>/command`: you can send the `ping` payload to force an update
  - `/ping/<host>/availability`: publishes `online` when starting the service or `offline`
    when the processes receives a `SIGINT` signal (e.g. by pressing Ctrl-C from the terminal).

## MQTT broker

The broker can be configured through the `BROKER`, `MQTT_USER` and `MQTT_PASSWORD` environment variables, assuming the default
port 1883. Feel free to submit a PR to support TLS and custom ports.

## Polling period

The polling period is configurable through the `POLLING_PERIOD` environment variable, value
is an integer to describe a period in seconds, e.g. `60` will poll hosts one after the other
every minute. Polling is disabled by default, if the variable isn't set or is set to a 
value of `-1`.

## Why does this app need to be run as root?

This app creates _raw_ network sockets (using ICMP, which is one level below the transport
layer) and doing so requires elevated privileges. Unprivileged users can only
create _dgram_ and _stream_ sockets.

Note that on a Linux system, the ping command always runs as root (the _setuid_ flag is set).

## Home Assistant Config

Configure an [MQTT Binary Sensor](https://www.home-assistant.io/integrations/binary_sensor.mqtt/)
for each host. This app is not HA-aware at all, and so you'll have to configure the sensors
manually. The `connectivity` and `presence` [device classes](https://www.home-assistant.io/integrations/binary_sensor/#device-class) 
are good choices. Here is an example of how you could use this program:

```yaml
mqtt:
  binary_sensor:
    - name: iPhone Connected To Wi-Fi
      unique_id: "iphone_connected_to_wifi_binary_sensor"
      state_topic: "/ping/192.168.0.11"
      availability:
        - topic: "ping/192.168.0.11/availability"
      device_class: connectivity
      expire_after: 900
      icon: "mdi:cellphone-nfc"
```
