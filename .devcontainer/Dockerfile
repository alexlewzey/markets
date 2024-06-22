FROM python:3.12-bullseye

WORKDIR /workspaces/setup

# Install system packages
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg \
    software-properties-common

# Download and install Terraform
RUN wget -O- https://apt.releases.hashicorp.com/gpg | \
    gpg --dearmor | \
    tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
RUN echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
    https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
    tee /etc/apt/sources.list.d/hashicorp.list
RUN apt update && apt-get install terraform

# Install python dependencies
COPY .pre-commit-config.yaml pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root && \
    git init . && \
    pre-commit install --install-hooks

# Install terraform-docs
RUN wget https://github.com/terraform-docs/terraform-docs/releases/download/v0.17.0/terraform-docs-v0.17.0-linux-amd64.tar.gz && \
    mkdir -p tmp && \
    tar -xzf terraform-docs-v0.17.0-linux-amd64.tar.gz -C tmp && \
    mv tmp/terraform-docs /usr/local/bin/

# Install tflint
RUN curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Install trivy
RUN wget https://github.com/aquasecurity/trivy/releases/download/v0.31.3/trivy_0.31.3_Linux-64bit.tar.gz && \
    tar -xzf trivy_0.31.3_Linux-64bit.tar.gz -C tmp && \
    mv tmp/trivy /usr/local/bin/