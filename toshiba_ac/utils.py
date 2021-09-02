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
import datetime

async def async_sleep_until_next_multiply_of_minutes(minutes):
    next = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    next_rounded = datetime.datetime(
        year=next.year,
        month=next.month,
        day=next.day,
        hour=next.hour,
        minute=next.minute // minutes * minutes,
        second=0,
        microsecond=0
    )

    await asyncio.sleep((next_rounded - datetime.datetime.now()).total_seconds())
