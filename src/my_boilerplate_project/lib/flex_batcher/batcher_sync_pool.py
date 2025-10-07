import asyncio

from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from typing import Callable, List

from .config import SyncPoolConfig
from .abstract import _BatcherAbstract, InputType, OutputType

class SyncPoolBatcher(_BatcherAbstract[InputType, OutputType]):
    """
    Batches requests, combines them into batches and processes sync worker function using a thread or process pool.
    It supports:
    - Request batching with max size and latency
    - Backpressure via queue size limit
    - Non-blocking, per-request Future return
    - Timeout and error propagation

    Run the batcher on the background:

    >>> shutdown_event = asyncio.Event()  # Define shutdown event
    >>> def some_worker_fn(batch: List[InputType]) -> List[OutputType]
    >>> batcher.run(some_worker_fn, shutdown_event)

    Usage:

    >>> batcher = SyncPoolBatcher[InputType, OutputType](config=SyncPoolConfig(...))
    >>> async def some_handler(some_dto_in: InputType):
    >>>     result = await batcher.process(some_dto_in)


    Gracefully shutdown:

    >>> shutdown_event.set()
    >>> batcher.shutdown()
    """

    _executor: Executor
    _config: SyncPoolConfig

    def __init__(self, config: SyncPoolConfig = None) -> None:
        super().__init__(config)

        # Choose worker execution model
        if self._config.worker_mode == "process":
            self._executor = ProcessPoolExecutor(
                max_workers=self._config.max_workers
            )
        else:
            self._executor = ThreadPoolExecutor(
                max_workers=self._config.max_workers,
            )

    async def _exec(
            self,
            worker_fn: Callable[[List[InputType]], List[OutputType]],
            batch: List[InputType]
    ) -> List[OutputType]:
        loop = asyncio.get_event_loop()

        return await asyncio.wait_for(
            loop.run_in_executor(self._executor, worker_fn, batch),
            timeout=self._config.max_timeout_ms / 1000,
        )

    def shutdown(self, wait: bool = True):
        """
        Cleanly shuts down the executor pool.
        """
        self._executor.shutdown(wait=wait)


