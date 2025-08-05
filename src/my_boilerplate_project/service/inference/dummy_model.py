import time

class DummyModel:
    def __init__(self) -> None:
        self.model = "dummy model predicts"

    def predict(self, batch: list[str]) -> list[str]:
        # Синхронный блокирующий вызов (например, torch/transformers)
        time.sleep(0.2)
        return [f"{self.model}: {x}" for x in batch]
