import asyncio
from abc import ABC, abstractmethod
from asyncio import Task

from typing import Optional, Callable, TypeVar, Generic, Tuple, List, Awaitable, Coroutine, Any

from .config import _BaseAbstractConfig

OutputType = TypeVar("OutputType")
InputType = TypeVar("InputType")

class _BatcherAbstract(ABC, Generic[InputType, OutputType]):
    """
    Abstract base class for flex batcher. Don't use this directly.
    It supports:
    - Request batching with max size and latency
    - Backpressure via queue size limit
    - Non-blocking, per-request Future return
    - Timeout and error propagation
    """

    _config: _BaseAbstractConfig
    _semaphore: asyncio.Semaphore
    _queue: asyncio.Queue[Tuple[InputType, asyncio.Future]]

    def __init__(
            self,
            config: Optional[_BaseAbstractConfig] = None
    ):
        # Load default config if not provided
        if config is None:
            config = _BaseAbstractConfig()
        self._config = config

        # Semaphore limits concurrency of active batches
        # self._semaphore = asyncio.Semaphore(self._config.max_workers * self._config.inflight_per_worker)
        self._semaphore = asyncio.Semaphore(10 * 2)

        # Internal request queue with overflow protection
        self._queue = asyncio.Queue(maxsize=self._config.max_queue_size)

    def run(
            self,
            worker_fn: Callable[[List[InputType]], Awaitable[List[OutputType]]],
            shutdown_event: asyncio.Event = None,
    ):
        """
        Starts the asynchronous background batch worker.

        Args:
            worker_fn: A callable that receives a batch (List[T]) and returns List[V].
                       Should be CPU- or IO-bound logic that can be safely parallelized.
            shutdown_event: Optional asyncio.Event used to gracefully stop the worker loop.
                            If None, an internal Event is created and never set,
                            meaning the worker runs until process termination.

        Returns:
            asyncio.Task that runs the batching loop.
            You can optionally store and cancel it manually if needed.
        """

        worker: Task[_T] = asyncio.create_task(self._batch_worker(
            worker_fn= worker_fn,
            shutdown_event = shutdown_event,
        ))

        return worker

    async def _batch_worker(
            self,
            worker_fn: Callable[[List[InputType]], List[OutputType]],
            shutdown_event: asyncio.Event = None,
    ):
        if shutdown_event is None:
            shutdown_event = asyncio.Event()

        # Timeout guard for full processing cycle
        io_timeout = (self._config.max_batch_latency_ms + self._config.max_timeout_ms + 100 ) / 1000

        while not shutdown_event.is_set():
            batch = []
            futures = []

            first_timeout = 0.1 # quick polling interval
            try:
                # Block until first item is ready or timeout
                item = await asyncio.wait_for(self._queue.get(), first_timeout)
                batch.append(item[0])
                futures.append(item[1])
            except asyncio.TimeoutError:
                continue  # No work, restart loop

            # Fill batch up to size or until latency timeout hits
            start = asyncio.get_running_loop().time()
            while len(batch) < self._config.max_batch_size:
                timeout_left = self._config.max_batch_latency_ms / 1000 - (asyncio.get_running_loop().time() - start)
                if timeout_left <= 0:
                    break
                try:
                    item = await asyncio.wait_for(self._queue.get(), timeout=timeout_left)
                    batch.append(item[0])
                    futures.append(item[1])
                except asyncio.TimeoutError:
                    break

            # Run worker_fn via executor, with semaphore and timeout control
            async with asyncio.timeout(io_timeout):  # ожидание доступа
                async with self._semaphore:
                    try:
                        results = await self._exec(worker_fn, batch)

                        # Resolve futures for individual clients
                        for fut, result in zip(futures, results):
                            if not fut.done():
                                fut.set_result(result)

                    except asyncio.CancelledError:
                        # On failure, fail all attached futures
                        for fut in futures:
                            if not fut.done():
                                fut.set_exception(asyncio.CancelledError())
                        raise

                    except Exception as e:
                        # On failure, fail all attached futures
                        for fut in futures:
                            if not fut.done():
                                fut.set_exception(e)
                        raise

    @abstractmethod
    async def _exec (
            self,
            worker_fn: Callable[[List[InputType]], List[OutputType]],
            batch: List[InputType]
    ) -> List[OutputType]: ...

    async def process(self, data: InputType) -> OutputType:
        """
        Submit a request to be batched. Returns the result asynchronously.
        May raise if queue is full.
        """
        if self._queue.full():
            raise RuntimeError("Batch queue overflowed")
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[OutputType] = loop.create_future()
        self._queue.put_nowait((data, fut))

        res: OutputType = await fut
        return res
