FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Create and use a virtual environment inside the container
RUN uv venv /app/.venv

# Set environment variables to use the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies (if applicable)
RUN uv pip install -r requirements.txt

# Entrypoint to start the server
CMD ["uv", "run", "src/mcp_weather_server/server-see.py"]
