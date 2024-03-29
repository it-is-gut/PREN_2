import asyncio

import pika
from mavsdk import System
from project.main.const import const
import atexit
"""
The service is run first. It sets up all of the flags and required parameters for the system to function 
correctly. This service always has to start first
"""

async def run():
    """
    The main method that is run once at the start of this service.
    :return: None
    """
    # first we set up the pika connection
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=const.CONNECTION_STRING))
    channel = connection.channel()
    # this declares the exchange if it doesn't exist, otherwise it just checks it
    channel.exchange_declare(exchange=const.EXCHANGE, exchange_type='topic')

    channel.queue_declare(const.INIT_QUEUE_NAME, exclusive=False)

    channel.queue_bind(
        exchange='main', queue=const.INIT_QUEUE_NAME, routing_key=const.INIT_BINDING_KEY
    )

    def at_exit():
        # send message to status that init module is not ready
        channel.basic_publish(
            exchange=const.EXCHANGE, routing_key=const.STATUS_BINDING_KEY,
            body=const.INIT_MODULE_FLAG_FALSE)

    atexit.register(at_exit)

    # send message to status that init module is ready
    channel.basic_publish(
        exchange=const.EXCHANGE, routing_key=const.STATUS_BINDING_KEY,
        body=const.INIT_MODULE_FLAG_TRUE)

    # log that connection to RabbitMQ was successful
    channel.basic_publish(exchange=const.EXCHANGE, routing_key=const.LOG_BINDING_KEY,
                          body="init:successfully connected to rabbitmq")

    # start the mavsdk-backend (on localhost) and connect to it
    system = System()
    await system.connect()
    channel.basic_publish(exchange=const.EXCHANGE, routing_key=const.LOG_BINDING_KEY,
                          body="init:successfully connected to local mavsdk backend")

    # loop through all connections and get the first that is connected
    # --> Must be our drone, because there are no other peripherals
    uuid = None
    async for state in system.core.connection_state():
        if state.is_connected:
            uuid = state.uuid
            break
    channel.basic_publish(exchange=const.EXCHANGE, routing_key=const.LOG_BINDING_KEY,
                          body=str.format("init:drone with UUID %r connected" % uuid))

    # now we try to arm the drone
    possible_to_arm = False
    while not possible_to_arm:
        try:
            await system.action.arm()
            possible_to_arm = True
            channel.basic_publish(exchange=const.EXCHANGE, routing_key=const.LOG_BINDING_KEY,
                                  body="init:successfully armed drone")
            await system.action.disarm()
            break
        except Exception as error:
            channel.basic_publish(exchange=const.EXCHANGE, routing_key=const.LOG_BINDING_KEY,
                                  body=str.format(
                                      "init:failed to arm drone: %r " % str(error)))
            channel.basic_publish(exchange=const.EXCHANGE, routing_key=const.STATUS_BINDING_KEY,
                                  body=const.INIT_PX4_FLAG_FALSE)
            # try to arm every 5 seconds
            await asyncio.sleep(5)

    # log that arming was successful
    channel.basic_publish(exchange=const.EXCHANGE, routing_key=const.LOG_BINDING_KEY,
                          body="init:arming test was successful")

    # publish the __px4_running flag to the status module
    channel.basic_publish(exchange=const.EXCHANGE, routing_key=const.STATUS_BINDING_KEY,
                          body=const.INIT_PX4_FLAG_TRUE)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())