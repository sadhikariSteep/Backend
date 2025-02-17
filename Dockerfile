# Dockerfile
# FROM continuumio/miniconda3
# Use an official Miniconda image with CUDA 11.8 support
FROM nvidia/cuda:11.8.0-base-ubuntu20.04

# Set the working directory
WORKDIR /backend

# Install Miniconda (for package management) and basic dependencies
RUN apt-get update  && apt-get install -y git wget \
    && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm -f /tmp/miniconda.sh \
    && /opt/conda/bin/conda init bash

# Set up the PATH for conda
ENV PATH="/opt/conda/bin:$PATH"

# Set the working directory
#WORKDIR /backend


# Copy environment.yml to the container
#COPY environment.yml .
COPY requirements.txt .

# Make RUN commands use `bash --login`:
SHELL ["/bin/bash", "--login", "-c"]

# Disable SSL verification for Conda, create the environment, and install dependencies
# conda config --set ssl_verify false && \
# Create Conda environment and install dependencies
RUN /bin/bash -c "source /opt/conda/etc/profile.d/conda.sh && \
    conda create -n bot python=3.10 -y && \
    conda activate bot && \
    conda install -c pytorch -c nvidia faiss-gpu=1.8.0 pytorch=*=*cuda* pytorch-cuda=11 numpy -y && \
    pip install -r requirements.txt"

# RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

COPY . .
# Make RUN commands use the new environment:
#SHELL ["conda", "run", "-n", "bot", "/bin/bash", "-c"]

# Expose the port the app runs on
EXPOSE 8000
# Specify the environment as the default for CMD/ENTRYPOINT
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "bot", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--reload"]
# Set environment variable for PostgreSQL host
#ENV DATABASE_HOST="db"

# Run FastAPI with Uvicorn
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Run create_tables.py and then start FastAPI
# CMD ["sh", "-c", "python app/scripts/create_tables.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
