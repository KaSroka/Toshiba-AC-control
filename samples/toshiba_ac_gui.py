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

import logging

toshiba_logger = logging.getLogger('toshiba_ac')
logging.basicConfig(level=logging.WARNING, format='[%(asctime)s] %(levelname)-8s %(name)s: %(message)s')
toshiba_logger.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
        self.populate_device_tab_enum(dev_tab, 'ac_status', ToshibaAcFcuState.AcStatus, dev_tab.device.set_ac_status, 0)
        self.populate_device_tab_enum(dev_tab, 'ac_mode', ToshibaAcFcuState.AcMode, dev_tab.device.set_ac_mode, 1)

        dev_tab.ac_temperature = tk.StringVar()

        temp_req = tk.IntVar()

        temp_label = ttk.Label(dev_tab.tab, textvariable=dev_tab.ac_temperature)
        temp_label.grid(column=0, row=2, padx=5, pady=0)
        temp_sb = ttk.Spinbox(dev_tab.tab,
                              textvariable=temp_req,
                              from_=5, to=30,
                              width=7)
        temp_sb.grid(column=1, row=2, padx=0, pady=0)
        temp_req.set(dev_tab.device.ac_temperature)
        temp_req.trace_add('write', lambda *_: self.loop.create_task(dev_tab.device.set_ac_temperature(temp_req.get())))


        self.populate_device_tab_enum(dev_tab, 'ac_fan_mode', ToshibaAcFcuState.AcFanMode, dev_tab.device.set_ac_fan_mode, 3)
        self.populate_device_tab_enum(dev_tab, 'ac_swing_mode', ToshibaAcFcuState.AcSwingMode, dev_tab.device.set_ac_swing_mode, 4)
        self.populate_device_tab_enum(dev_tab, 'ac_power_selection', ToshibaAcFcuState.AcPowerSelection, dev_tab.device.set_ac_power_selection, 5)
        self.populate_device_tab_enum(dev_tab, 'ac_merit_b_feature', ToshibaAcFcuState.AcMeritBFeature, dev_tab.device.set_ac_merit_b_feature, 6)
        self.populate_device_tab_enum(dev_tab, 'ac_merit_a_feature', ToshibaAcFcuState.AcMeritAFeature, dev_tab.device.set_ac_merit_a_feature, 7)
        self.populate_device_tab_enum(dev_tab, 'ac_air_pure_ion', ToshibaAcFcuState.AcAirPureIon, dev_tab.device.set_ac_air_pure_ion, 8)

        dev_tab.ac_indoor_temperature = tk.StringVar()

        i_temp_label = ttk.Label(dev_tab.tab, textvariable=dev_tab.ac_indoor_temperature)
        i_temp_label.grid(column=0, row=9, padx=5, pady=0)

        dev_tab.ac_outdoor_temperature = tk.StringVar()

        o_temp_label = ttk.Label(dev_tab.tab, textvariable=dev_tab.ac_outdoor_temperature)
        o_temp_label.grid(column=0, row=10, padx=5, pady=0)

        dev_tab.ac_self_cleaning = tk.StringVar()

        self_cleaning_label = ttk.Label(dev_tab.tab, textvariable=dev_tab.ac_self_cleaning)
        self_cleaning_label.grid(column=0, row=11, padx=5, pady=0)

        dev_tab.ac_energy_consumption = tk.StringVar()

        energy_label = ttk.Label(dev_tab.tab, textvariable=dev_tab.ac_energy_consumption)
        energy_label.grid(column=0, row=12, padx=5, pady=0)

        self.update_ac_state(dev_tab)

    def update_ac_state_entry(self, dev_tab, entry_name, title):
        getattr(dev_tab, entry_name).set(f'{title}: {getattr(dev_tab.device, entry_name).name.title().replace("_", " ")}')

    def update_ac_state(self, dev_tab):
        self.update_ac_state_entry(dev_tab, 'ac_status', 'Power')
        self.update_ac_state_entry(dev_tab, 'ac_mode', 'Mode')
        dev_tab.ac_temperature.set(f'Temperature: {dev_tab.device.ac_temperature}')
        self.update_ac_state_entry(dev_tab, 'ac_fan_mode', 'Fan mode')
        self.update_ac_state_entry(dev_tab, 'ac_swing_mode', 'Swing mode')
        self.update_ac_state_entry(dev_tab, 'ac_power_selection', 'Power selection')
        self.update_ac_state_entry(dev_tab, 'ac_merit_b_feature', 'Merit B feature')
        self.update_ac_state_entry(dev_tab, 'ac_merit_a_feature', 'Merit A feature')
        self.update_ac_state_entry(dev_tab, 'ac_air_pure_ion', 'Pure ion')
        dev_tab.ac_indoor_temperature.set(f'Indoor temperature: {dev_tab.device.ac_indoor_temperature}')
        dev_tab.ac_outdoor_temperature.set(f'Outdoor temperature: {dev_tab.device.ac_outdoor_temperature}')
        self.update_ac_state_entry(dev_tab, 'ac_self_cleaning', 'Self cleaning')
        if dev_tab.device.ac_energy_consumption:
            dev_tab.ac_energy_consumption.set(f'Energy used {dev_tab.device.ac_energy_consumption.energy_wh}Wh since {dev_tab.device.ac_energy_consumption.since}')

    def dev_state_changed(self, dev):
        self.update_ac_state(self.devices[dev])

    async def init(self):
        self.device_manager = ToshibaAcDeviceManager(self.loop, self.user, self.password, '3e6e4eb5f0e5aa40')
        sas_token = await self.device_manager.connect()
        logger.debug(f'AMQP SAS token: {sas_token}')

        devices = await self.device_manager.get_devices()

        for device in devices:
            tab = ttk.Frame(self.tab_control)
            dev_tab = DeviceTab(device, tab)
            self.populate_device_tab(dev_tab)
            self.devices[device] = dev_tab

            device.on_state_changed_callback.add(self.dev_state_changed)
            device.on_energy_consumption_changed_callback.add(self.dev_state_changed)

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
