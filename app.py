#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
import ischedule
import logging
import os
import paho.mqtt.client as mqtt
import signal
import sys

# Local packages
from scheduler import Scheduler
from pinger import Pinger



class App:
    """
    This MQTT Subscriber subscribes to the MQTT ping/<ip>/command topic for each device, listening for a "ping" payload,
    then subsequently executes an ICMP ping to that IP address, and sends "on" (ping came back) or "off" (no response)
    to the ping/<ip> topic.

    While this documentation refers to IP addresses, a resolvable hostname can be substituted as well.
    """

    def __init__(self, devices, broker, port=1883, user='', password=''):
        """
        Connects to the MQTT broker, which will also trigger it to subscribe to the appropriate topics if successful.
        
        Parameters
        ----------
        devices : list
            a list of IP addresses or hostnames

        broker : string
            The broker hostname or IP address

        port : int, optional
            The port number of the broker. 1883 by default. 8883 (TLS) might work but it has not been tested.

        user : string
            Username to authenticate to MQTT

        password : string
            Password to authenticate to MQTT
        """

        self.devices = devices
        self.pinger = Pinger()
        self.executor = ThreadPoolExecutor()

        self.mqtt_client = mqtt.Client()
        if user != '' and password != '':
            self.mqtt_client.username_pw_set(user, password)
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message

        self.mqtt_client.connect(broker, port)


    def loop_forever(self):
        self.mqtt_client.loop_forever()


    def on_mqtt_connect(self, client, userdata, flags, rc):
        logging.info("Connected to MQTT with result code " + str(rc))

        # Subscribe to topics
        command_topics = [('ping/' + ip + '/command', 2) for ip in self.devices]
        self.mqtt_client.subscribe(command_topics)

        # Initial updates
        logging.info('Updating all targets')
        self.update_all_ips()


    def on_mqtt_message(self, client, userdata, msg):
        logging.debug(msg.topic + ": " + str(msg.payload))

        topic_components = msg.topic.split('/')
        ip = topic_components[1]

        payload = msg.payload.decode('utf-8')
        logging.debug('Received payload %s', payload)

        if msg.topic.endswith('/command'):
            self.on_command_message(ip, payload)
        else:
            logging.warning('No action defined for topic ' + msg.topic)


    def on_command_message(self, ip, payload):
        if payload == 'ping':
            self.update_ip(ip)
        else:
            logging.warning("Unknown payload: " + payload)


    def update_ip(self, ip):
        self.executor.submit(self._do_update_ip, ip)


    def _do_update_ip(self, ip):
        logging.debug('Updating %s', ip)
        state = self.pinger.ping(ip)
        logging.debug('%s is %s', ip, 'responding' if state else 'timing out')
        self.publish_new_state(ip, state)
        self.announce_online(ip)


    def update_all_ips(self):
        for ip in self.devices:
            self.update_ip(ip)


    def publish_new_state(self, ip, state):
        payload = 'ON' if state else 'OFF'
        topic = 'ping/' + ip 
        self.mqtt_client.publish(topic, payload=payload, retain=False)


    def announce_online(self, ip):
        self.mqtt_client.publish('ping/' + ip + '/availability', payload='online', retain=False)


    def announce_offline(self):
        for ip in self.devices:
            self.mqtt_client.publish('ping/' + ip + '/availability', payload='offline', retain=False)
   


app = None

def signal_handler(signal_received, frame):
    logging.info("SIGING or CTRL-C detected. Exiting gracefully")
    app.announce_offline()
    sys.exit(0)


if __name__ == '__main__':
    level = logging.INFO
    if 'LOG_LEVEL' in os.environ:
        if os.environ['LOG_LEVEL'] == 'DEBUG':
            level = logging.DEBUG
        elif os.environ['LOG_LEVEL'] == 'INFO':
            level = logging.INFO
        elif os.environ['LOG_LEVEL'] == 'WARN':
            level = logging.WARN
        else:
            raise Exception('Unknown log level: ' + os.environ['LOG_LEVEL'])
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=level)
    
    # TARGETS environment variable
    # contains a comma-separated list of IP addresses or hostnames to ping.
    # For example: 
    #   TARGETS=192.168.0.1,printer.local
    ips = os.environ['TARGETS'].split(',')

    # BROKER environment variable
    # specifies the broker IP address or hostname. See App.__init__ pydoc for more information if you wish to set a different port
    # than the default (1883).
    broker = os.environ['BROKER']
    
    # MQTT_USER environment variable
    # specifies the username to connect to MQTT broker
    mqtt_user = os.environ['MQTT_USER']
    
    # MQTT_PASSWORD environment variable
    # specifies the password to connect to MQTT broker
    mqtt_password = os.environ['MQTT_PASSWORD']
    
    app = App(ips, broker, 1883, mqtt_user, mqtt_password)

    # POLLING_PERIOD environment variable, in seconds. Disabled by default.
    polling_period = int(os.environ['POLLING_PERIOD'] if 'POLLING_PERIOD' in os.environ else -1)
    if polling_period > 0:
        logging.info('Periodic polling enabled. Will refresh all targets every %d seconds.', polling_period)
        Scheduler().run_periodically(target=app.update_all_ips, period=float(polling_period))

    # Handle exit signal so we can send the "offline" message in the availability topic
    signal.signal(signal.SIGINT, signal_handler)

    # To test this app, you can use mosquitto_pub and mosquitto_sub. For example:
    # mosquitto_sub -h 192.168.0.2 -t 'ping/192.168.0.100'
    # mosquitto_sub -h 192.168.0.2 -t 'ping/192.168.0.100/availability'
    # mosquitto_pub -h 192.168.0.2 -t 'ping/192.168.0.100/command' -m 'ping'

    # THIS APP MUST BE RUN WITH ROOT PRIVILEGES.
    # See https://github.com/alessandromaggio/pythonping
    # TL;DR Sending ICMP packets is not allowed in userspace.

    app.loop_forever()
