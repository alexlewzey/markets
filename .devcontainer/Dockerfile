FROM python:3.13-bullseye

WORKDIR /workspaces/setup


# Install required packages
RUN apt-get update && apt-get install -y \
    curl \
    unzip

# Install Terraform
RUN curl -fsSL https://releases.hashicorp.com/terraform/1.7.4/terraform_1.7.4_linux_amd64.zip -o terraform.zip \
    && unzip terraform.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform.zip

# Install python dependencies
RUN pip install poetry

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