# Copyright 2021 Kamil Sroka

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import os
import sys

from toshiba_ac.device import ToshibaAcDevice
from toshiba_ac.fcu_state import ToshibaAcFcuState

async def ainput(string: str) -> str:
    await asyncio.get_event_loop().run_in_executor(
            None, lambda s=string: sys.stdout.write(s))
    return await asyncio.get_event_loop().run_in_executor(
            None, lambda: sys.stdin.readline().strip('\n'))

async def main():
    device_id = os.environ['TOSHIBA_DEVICE_ID']
    ac_id = os.environ['TOSHIBA_AC_ID']
    shared_access_key = os.environ['TOSHIBA_SHARED_ACCESS_KEY']

    device = ToshibaAcDevice(device_id, shared_access_key, ac_id)

    await device.connect()

    print(f'Connected to AC')

    async def simple_cli():
        while True:
            selection = await ainput("Press Q to quit, on/off to control AC power\n")

            if selection == "Q" or selection == "q":
                print("Quitting...")
                return

            elif selection == 'off':
                await device.set_ac_status(ToshibaAcFcuState.AcStatus.OFF)

            elif selection == 'on':
                await device.set_ac_status(ToshibaAcFcuState.AcStatus.ON)

    await simple_cli()
    await device.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
