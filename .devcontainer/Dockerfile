FROM mcr.microsoft.com/devcontainers/typescript-node:22-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    python3.11-dev \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir \
        awscli \
        ruff \
    && ln -s /opt/venv/bin/aws /usr/local/bin/aws \
    && ln -s /opt/venv/bin/ruff /usr/local/bin/ruff \
    && rm -rf ~/.cache/pip

RUN npm install -g aws-cdk
