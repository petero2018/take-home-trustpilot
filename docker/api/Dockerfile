# Base image arguments
ARG PYTHON_VERSION
ARG PYTHON_FLAVOUR
ARG DOCKER_REPOSITORY

# Base Python image
FROM ${DOCKER_REPOSITORY}:${PYTHON_VERSION}-${PYTHON_FLAVOUR}
LABEL org.opencontainers.image.authors="oszi <osztodipeter@gmail.com>"
ARG POETRY_VERSION

# Environment configuration
ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=${POETRY_VERSION} \
    PATH="/root/.local/bin:$PATH" \
    PORT=8000

# Install system dependencies and Poetry
RUN apt-get update && \
    apt-get install -y curl git build-essential libssl-dev zlib1g-dev && \
    apt-get install -y libbz2-dev libreadline-dev libsqlite3-dev wget && \
    curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION} && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy Poetry project definition first to leverage Docker layer caching
COPY tp_api_project/pyproject.toml tp_api_project/poetry.lock* ./tp_api_project/

# Ensure the lock file matches dependencies (regenerate on mismatch)
RUN poetry --directory tp_api_project lock --no-update || poetry --directory tp_api_project lock

# Install API project dependencies (without installing the project itself)
RUN poetry --directory tp_api_project install --no-root

# Copy application code and shared assets
COPY tp_api_project/ ./tp_api_project/
COPY data/ ./data/

# Expose HTTP port
EXPOSE 8000

# Default runtime command
CMD ["poetry", "--directory", "tp_api_project", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
