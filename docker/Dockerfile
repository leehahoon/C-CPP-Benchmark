FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    clang \
    cmake \
    cppcheck \
    curl \
    default-libmysqlclient-dev \
    git \
    libssl-dev \
    python3 \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4-openssl-dev \
    libsqlite3-dev \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/benchmark-venv \
    && /opt/benchmark-venv/bin/pip install --no-cache-dir gdown==6.4.2

ENV PATH="/opt/benchmark-venv/bin:${PATH}"

WORKDIR /workspace
