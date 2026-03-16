FROM us-docker.pkg.dev/vertex-ai/training/pytorch-tpu.2-1.cp310:latest

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /src
WORKDIR /src

RUN uv pip install --system .

ENTRYPOINT ["python3", "scripts/main.py"]