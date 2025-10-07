import asyncio
import time
import pytest

from .batcher_async import AsyncBatcher
from .config import AsyncConfig

class DummyModel:
    def __init__(self) -> None:
        self.model = "dummy model predicts"

    def predict(self, batch: list[[float]]) -> list[[float]]:
        # Синхронный блокирующий вызов (например, torch/transformers)
        time.sleep(0.2)
        return batch


# Параметризация
@pytest.mark.asyncio
@pytest.mark.parametrize("inputs, expected", [
    ([1, 2, 3], [2, 4, 6]),
    ([10], [20]),
    ([], []),
])
async def test_async_batcher_processing(inputs, expected):
    # Настройка батчера
    config = AsyncConfig(
        max_batch_latency_ms=50,
        max_timeout_ms=100,
        max_batch_size=10,
        max_queue_size=10,
    )
    batcher = AsyncBatcher[int, int](config=config)

    # Обработчик
    async def double(batch: list[int]) -> list[int]:
        return [x * 2 for x in batch]

    # Событие остановки и запуск раннера
    shutdown_event = asyncio.Event()
    runner_task = batcher.run(double, shutdown_event)

    # Добавляем данные в батчер
    results = await asyncio.gather(*[batcher.process(x) for x in inputs])

    # Завершаем раннер
    shutdown_event.set()
    await runner_task

    # Проверка
    assert results == expected