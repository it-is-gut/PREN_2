#!/usr/bin/env python3

import asyncio
from mavsdk import System


async def run():

    drone = System()
    #await drone.connect(system_address="udp://:14540")
    await drone.connect(system_address="serial://dev/serial0 [:921600]")

    print("Waiting for drone...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone discovered with UUID: {state.uuid}")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()

    await asyncio.sleep(5)

    print("-- Landing")
    await drone.action.land()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())