import asyncio

from typing import Callable, Awaitable, List

from .config import AsyncConfig
from .abstract import _BatcherAbstract, InputType, OutputType

class AsyncBatcher(_BatcherAbstract[InputType, OutputType]):
    def __init__(self, config: AsyncConfig = None) -> None:
        if config is None:
            config = AsyncConfig()
        super().__init__(config)

    async def _exec(
            self,
            worker_fn: Callable[[List[InputType]], Awaitable[List[OutputType]]],
            batch: List[InputType]
    ) -> List[OutputType]:
        return await asyncio.wait_for(
            worker_fn(batch),
            timeout=self._config.max_timeout_ms / 1000,
        )