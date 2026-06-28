FROM python:3.12-slim

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency files first so this layer is cached unless deps change
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Copy the rest of the project
COPY . .

EXPOSE 5000

# Default command runs the dashboard.
# Override with `docker run ... uv run update_icon.py` to run the script instead.
CMD ["uv", "run", "app.py"]
