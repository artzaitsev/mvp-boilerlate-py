FROM python:3.12-slim

# Аргументы сборки
ARG ENTRYPOINT=api

# Устанавливаем Poetry
RUN pip install poetry

# Работаем в рабочей директории
WORKDIR /app

# Копируем только метафайлы (для кеша зависимостей)
COPY pyproject.toml poetry.lock ./

# Poetry конфиг без виртуального окружения
RUN poetry config virtualenvs.create false

# Устанавливаем только нужные группы зависимостей
RUN poetry install --no-root --with $ENTRYPOINT

# Копируем исходный код проекта (после install — для кэша)
COPY src/ ./src/
COPY .env ./

# Устанавливаем переменные среды (если нужно)
ENV PYTHONPATH=/app/src

# Запускаем выбранный entrypoint
CMD ["python", "-m", "my_project.entrypoint.${ENTRYPOINT}"]
