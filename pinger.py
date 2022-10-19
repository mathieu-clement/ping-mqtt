#!/usr/bin/env python3

import pythonping as pp

from os import environ as env

PING_COUNT = env['PING_COUNT'] if 'PING_COUNT' in env else 30
TIMEOUT = env['PING_TIMEOUT'] if 'PING_TIMEOUT' in env else 1

class Pinger:
    def ping(self, ip, count=6, timeout=5):
        """
        Performs a number (count) of ICMP Pings until it gets a positive response,
        else returns False.
        """
        for i in range(0, count):
            pong = self.do_ping(ip, timeout)
            if pong:
                return True
        return False


    def do_ping(self, ip, timeout):
        return pp.ping(ip, count=1, timeout=timeout).success()
