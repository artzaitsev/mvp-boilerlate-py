from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class _BaseAbstractConfig:
    """
    Configuration for flexible batcher.

    - worker_mode: Execution mode for batch processing. Default is "thread".

        - "thread": Uses ThreadPoolExecutor. Suitable for I/O-bound or lightweight CPU tasks.
        - "process": Uses ProcessPoolExecutor. Suitable for CPU-bound tasks like ML inference.

    - max_batch_latency_ms: Max allowed latency before a batch is processed. Default is 100.
    - max_batch_size: Max number of requests per batch. Default is 10.
    - max_workers: Max number of parallel processes. Default is 1.
    - max_queue_size: Max number of requests in the queue. Default is 1.
    """
    max_timeout_ms: int = 100
    max_batch_latency_ms: int = 100
    max_batch_size: int = 16
    max_queue_size: int = 1000

@dataclass
class SyncPoolConfig(_BaseAbstractConfig):
    """
    Configuration for flexible batcher.

    - worker_mode: Execution mode for batch processing. Default is "thread".

        - "thread": Uses ThreadPoolExecutor. Suitable for I/O-bound or lightweight CPU tasks.
        - "process": Uses ProcessPoolExecutor. Suitable for CPU-bound tasks like ML inference.

    - max_batch_latency_ms: Max allowed latency before a batch is processed. Default is 100.
    - max_batch_size: Max number of requests per batch. Default is 10.
    - max_workers: Max number of parallel processes. Default is 1.
    - max_queue_size: Max number of requests in the queue. Default is 1.
    """
    worker_mode: Literal["process", "thread"] = "thread"
    max_workers: Optional[int] = 1
    inflight_per_worker: int = 3

@dataclass
class AsyncConfig(_BaseAbstractConfig):
    """
    Configuration for flexible batcher.

    - worker_mode: Execution mode for batch processing. Default is "thread".

        - "thread": Uses ThreadPoolExecutor. Suitable for I/O-bound or lightweight CPU tasks.
        - "process": Uses ProcessPoolExecutor. Suitable for CPU-bound tasks like ML inference.

    - max_batch_latency_ms: Max allowed latency before a batch is processed. Default is 100.
    - max_batch_size: Max number of requests per batch. Default is 10.
    - max_workers: Max number of parallel processes. Default is 1.
    - max_queue_size: Max number of requests in the queue. Default is 1.
    """
    ...