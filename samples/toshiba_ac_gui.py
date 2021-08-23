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
import tkinter as tk
from tkinter import ttk

import argparse
import os
from toshiba_ac.fcu_state import ToshibaAcFcuState

from toshiba_ac.device_manager import ToshibaAcDeviceManager

class DeviceTab:
    def __init__(self, device, tab):
        self.device = device
        self.tab = tab

class App(tk.Tk):
    def __init__(self, loop, user, password, refresh_interval=1/20):
        super().__init__()
        self.user = user
        self.password = password
        self.title('Toshiba AC')
        self.loop = loop
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.updater_task = self.loop.create_task(self.updater(refresh_interval))
        self.tab_control = ttk.Notebook()
        self.devices = {}

        self.loop.create_task(self.init())

    def populate_device_tab_enum(self, dev_tab, var_name, enum, setter, row):
        string_var = tk.StringVar()
        setattr(dev_tab, var_name, string_var)

        label = ttk.Label(dev_tab.tab, textvariable=string_var)
        label.grid(column=0, row=row, padx=5, pady=0)

        options = [e.name for e in enum if e.name not in ['NONE', 'INVALID']]
        for i, option in enumerate(options, start=1):
            btn = ttk.Button(dev_tab.tab, text=option.title().replace('_', ' '), command=lambda opt=option: self.loop.create_task(setter(enum[opt])))
            btn.grid(column=i, row=row, padx=0, pady=0)

    def populate_device_tab(self, dev_tab):
        tab = dev_tab.tab

        self.populate_device_tab_enum(dev_tab, 'ac_status', ToshibaAcFcuState.AcStatus, dev_tab.device.set_ac_status, 0)
        self.populate_device_tab_enum(dev_tab, 'ac_mode', ToshibaAcFcuState.AcMode, dev_tab.device.set_ac_mode, 1)

        dev_tab.ac_temperature = tk.StringVar()

        temp_req = tk.IntVar()

        temp_label = ttk.Label(dev_tab.tab, textvariable=dev_tab.ac_temperature)
        temp_label.grid(column=0, row=2, padx=5, pady=0)
        temp_sb = ttk.Spinbox(dev_tab.tab,
                              textvariable=temp_req,
                              from_=17, to=30,
                              width=7)
        temp_sb.grid(column=1, row=2, padx=0, pady=0)
        temp_req.set(dev_tab.device.ac_temperature.name)
        temp_req.trace_add('write', lambda *_: self.loop.create_task(dev_tab.device.set_ac_temperature(temp_req.get())))


        self.populate_device_tab_enum(dev_tab, 'ac_fan_mode', ToshibaAcFcuState.AcFanMode, dev_tab.device.set_ac_fan_mode, 3)

        self.update_ac_state(dev_tab)

    def update_ac_state(self, dev_tab):
        dev_tab.ac_status.set(f'Pwer: {dev_tab.device.ac_status.name.title()}')
        dev_tab.ac_mode.set(f'Mode: {dev_tab.device.ac_mode.name.title()}')
        dev_tab.ac_temperature.set(f'Temperature: {dev_tab.device.ac_temperature.name}')
        dev_tab.ac_fan_mode.set(f'Fan mode: {dev_tab.device.ac_fan_mode.name.title().replace("_", " ")}')

    def dev_state_changed(self, dev):
        self.loop.call_soon_threadsafe(self.update_ac_state, self.devices[dev])

    async def init(self):
        self.device_manager = ToshibaAcDeviceManager(self.user, self.password)
        await self.device_manager.connect()
        devices = await self.device_manager.get_devices()

        for device in devices:
            tab = ttk.Frame(self.tab_control)
            dev_tab = DeviceTab(device, tab)
            self.populate_device_tab(dev_tab)
            self.devices[device] = dev_tab

            device.on_state_changed = self.dev_state_changed

            self.tab_control.add(tab, text=f'{device.name}')

        self.tab_control.pack(expand=1, fill='both')

    async def updater(self, interval):
        while True:
            self.update()
            await asyncio.sleep(interval)

    def close(self):
        self.updater_task.cancel()
        self.loop.create_task(self.device_manager.shutdown()).add_done_callback(self.cleanup)

    def cleanup(self, _):
        self.loop.stop()

class EnvDefault(argparse.Action):
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if not default and envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required,
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

def parse_cred():

    parser = argparse.ArgumentParser(description='CLI for Toshiba AC')
    parser.add_argument("--user",
                        metavar='user_name',
                        action=EnvDefault,
                        envvar='TOSHIBA_USER',
                        help='Toshiba Home AC user name (can also be specified using TOSHIBA_USER environment variable)')
    parser.add_argument("--pass",
                        metavar='password',
                        dest='password',
                        action=EnvDefault,
                        envvar='TOSHIBA_PASS',
                        help='Toshiba Home AC password (can also be specified using TOSHIBA_PASS environment variable)')

    cred = parser.parse_args()

    return cred.user, cred.password

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = App(loop, *parse_cred())
    loop.run_forever()
