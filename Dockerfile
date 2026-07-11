FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# System deps
RUN apt update && apt install -y \
    python3 python3-pip \
    git curl openssh-client build-essential \
    && apt clean

# Yarn
RUN corepack enable

# Workdir
WORKDIR /workspace

RUN python3 -m pip install --upgrade pip
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["/bin/bash"]
