# Use Python 3.9 slim image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install AWS CLI for ARM64
RUN apt-get update && \
    apt-get install -y curl unzip && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -f awscliv2.zip && \
    apt-get clean

# Install dependencies for fridge_mgr
WORKDIR /app/src/fridge_mgr
RUN python -m venv venv
RUN venv/bin/pip install -r local_dependencies.txt
RUN pip install -r lambda_dependencies.txt -t lambda_dependencies

EXPOSE 80

WORKDIR /app
CMD ["tail", "-f", "/dev/null"]