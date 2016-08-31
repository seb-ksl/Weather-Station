#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal


class GracefulExit(object):
    def __init__(self):
        self.kill = False
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signal, frame):
        self.kill = True
