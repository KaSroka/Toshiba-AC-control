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
import functools
import logging
import random
import typing as t
from enum import Enum

logger = logging.getLogger(__name__)


async def async_sleep_until_next_multiply_of_minutes(minutes: int, backoff_s: float = 300) -> None:
    next = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    next_rounded = datetime.datetime(
        year=next.year,
        month=next.month,
        day=next.day,
        hour=next.hour,
        minute=next.minute // minutes * minutes,
        second=0,
        microsecond=0,
    )

    backoff = random.uniform(0, backoff_s)

    await asyncio.sleep((next_rounded - datetime.datetime.now()).total_seconds() + backoff)


def pretty_enum_name(enum: Enum) -> str:
    return enum.name.title().replace("_", " ")


# Define a generic type variable that will capture the return type of the retried function
R = t.TypeVar("R")

# Define a ParamSpec to capture the parameters of the retried function
P = t.ParamSpec("P")


class RetryJitterMode(str, Enum):
    # Full jitter: pick a delay uniformly from [0, cap].
    # Best at spreading retries broadly across many clients.
    FULL = "full"
    # Equal jitter: pick a delay uniformly from [cap/2, cap].
    # Avoids very short retries while preserving randomness.
    EQUAL = "equal"


def _compute_exponential_backoff_delay(
    *,
    backoff: float,
    attempt: int,
    max_backoff: float,
    growth_factor: float = 2.0,
    jitter_mode: RetryJitterMode = RetryJitterMode.FULL,
) -> float:
    capped_backoff = min(max_backoff, backoff * (growth_factor ** (attempt - 1)))

    if jitter_mode == RetryJitterMode.EQUAL:
        return random.uniform(capped_backoff / 2, capped_backoff)

    return random.uniform(0, capped_backoff)


def retry_with_timeout(
    *,
    timeout: float,
    retries: int,
    backoff: float,
    max_backoff: float = 300,
    growth_factor: float = 2.0,
    jitter_mode: RetryJitterMode = RetryJitterMode.FULL,
) -> t.Callable[[t.Callable[P, t.Awaitable[R]]], t.Callable[P, t.Awaitable[R]]]:
    def decorator(func: t.Callable[P, t.Awaitable[R]]) -> t.Callable[P, t.Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            attempt = 0
            while True:
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                except asyncio.TimeoutError:
                    attempt += 1
                    if attempt < retries + 1:
                        logger.info("Timeout exception. Will retry after backoff.")
                        bk = _compute_exponential_backoff_delay(
                            backoff=backoff,
                            attempt=attempt,
                            max_backoff=max_backoff,
                            growth_factor=growth_factor,
                            jitter_mode=jitter_mode,
                        )
                        await asyncio.sleep(bk)
                    else:
                        raise

        return wrapper

    return decorator


def retry_on_exception(
    *,
    retries: int,
    backoff: float,
    max_backoff: float = 300,
    growth_factor: float = 2.0,
    jitter_mode: RetryJitterMode = RetryJitterMode.FULL,
    exceptions: t.Type[BaseException] | t.Tuple[t.Type[BaseException], ...],
    should_retry: t.Optional[t.Callable[[BaseException], bool]] = None,
) -> t.Callable[[t.Callable[P, t.Awaitable[R]]], t.Callable[P, t.Awaitable[R]]]:
    def decorator(func: t.Callable[P, t.Awaitable[R]]) -> t.Callable[P, t.Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            attempt = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if should_retry is not None and not should_retry(e):
                        raise

                    attempt += 1
                    if attempt < retries + 1:
                        bk = _compute_exponential_backoff_delay(
                            backoff=backoff,
                            attempt=attempt,
                            max_backoff=max_backoff,
                            growth_factor=growth_factor,
                            jitter_mode=jitter_mode,
                        )
                        error_preview = str(e)
                        if len(error_preview) > 200:
                            error_preview = error_preview[:197] + "..."
                        logger.info(
                            f"Known exception occurred ({type(e).__name__}: {error_preview}). "
                            f"Retry {attempt}/{retries} after backoff {bk:.2f}s."
                        )
                        await asyncio.sleep(bk)
                    else:
                        raise

        return wrapper

    return decorator


T = t.TypeVar("T")  # Generic type variable for devices


class ToshibaAcCallback(t.Generic[T]):
    def __init__(self) -> None:
        self.callbacks: t.List[t.Callable[[T], t.Optional[t.Awaitable[None]]]] = []

    def add(self, callback: t.Callable[[T], t.Optional[t.Awaitable[None]]]) -> bool:
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            return True

        return False

    def remove(self, callback: t.Callable[[T], t.Optional[t.Awaitable[None]]]) -> bool:
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            return True

        return False

    async def __call__(self, device: T) -> None:
        asyncs = []

        for callback in self.callbacks:
            if asyncio.iscoroutinefunction(callback):
                asyncs.append(t.cast(t.Awaitable[None], callback(device)))
            else:
                callback(device)

        await asyncio.gather(*asyncs)
