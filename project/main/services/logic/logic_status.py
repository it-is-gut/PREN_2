#!/usr/bin/env python3
import json
import threading
import time
from threading import Lock

import pika
from mavsdk import (OffboardError, PositionNedYaw)

from project.main.const import const
import atexit



def callbackStatus(ch, method, properties, body):
    message_parts = body.decode('utf8').split(":")

    if message_parts[2].__eq__(" True"):
        const.systemStateOk = True
    else:
        const.systemStateOk = False
    print("system_ok: %r" % const.systemStateOk)

class LogicStatus(threading.Thread):
    """
    This is the class that handles the receiving and sending of statuses corresponding to the logic service
    """
    systemStateOk = True

    def __init__(self):
        threading.Thread.__init__(self)
        self.connectionStatus = None
        self.channelStatus = None
        self.lock = Lock()
        self.channel = None

    def declareQueueStatus(self):
        """
        Setups up the queue to send and receive status flags from/to the status service
        :return: None
        """
        self.connectionStatus = pika.BlockingConnection(
            pika.ConnectionParameters(host=const.CONNECTION_STRING))
        self.channel = self.connectionStatus.channel()
        self.channelStatus = self.connectionStatus.channel()
        # declare queue just for status messages (system_ok)
        self.channel.queue_declare(const.LOGIC_STATUS_QUEUE_NAME, exclusive=False)
        self.channel.queue_bind(
            exchange='main', queue=const.LOGIC_STATUS_QUEUE_NAME, routing_key=const.LOGIC_STATUS_BINDING_KEY
        )

        # send message to status that logic module is ready
        self.channel.basic_publish(
            exchange=const.EXCHANGE, routing_key=const.STATUS_BINDING_KEY,
            body=const.LOGIC_MODULE_FLAG_TRUE)
        self.checkOverallStatus()

    def checkOverallStatus(self):
        """
        Checks the overall status of the system and reacts accordingly.
        :return:
        """
        print(' [*] Waiting for overall values. To exit press CTRL+C')
        self.channelStatus.basic_consume(queue=const.LOGIC_STATUS_QUEUE_NAME,
                                         on_message_callback=callbackStatus, auto_ack=True)
        self.channelStatus.start_consuming()

    def run(self):
        self.declareQueueStatus()

        def at_exit():
            # send message to status that logic module is not ready
            self.channel.basic_publish(
                exchange=const.EXCHANGE, routing_key=const.STATUS_BINDING_KEY,
                body=const.LOGIC_MODULE_FLAG_FALSE)

        atexit.register(at_exit)

def main():
    thread1 = LogicStatus()
    thread1.start()



