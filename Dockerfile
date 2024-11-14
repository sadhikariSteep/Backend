# Dockerfile
FROM continuumio/miniconda3

# Set the working directory
WORKDIR /BACKEND

# Make RUN commands use `bash --login`:
SHELL ["/bin/bash", "--login", "-c"]
# Copy environment.yml to the container
#COPY environment.yml .
COPY requirements.txt .

# Disable SSL verification for Conda, create the environment, and install dependencies
# conda config --set ssl_verify false && \
RUN conda create -n bot python=3.9 -y
RUN conda init bash 
RUN conda activate bot
RUN conda install -c pytorch -c nvidia faiss-gpu=1.8.0 pytorch=*=*cuda* pytorch-cuda=11 numpy -y 
#RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
RUN pip install -r requirements.txt

# RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

# Copy the app and main FastAPI entrypoint
COPY . .
# Make RUN commands use the new environment:
#SHELL ["conda", "run", "-n", "bot", "/bin/bash", "-c"]

# Expose the port the app runs on
EXPOSE 8000
# Specify the environment as the default for CMD/ENTRYPOINT
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "bot", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
# Set environment variable for PostgreSQL host
#ENV DATABASE_HOST="db"

# Run FastAPI with Uvicorn
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Run create_tables.py and then start FastAPI
# CMD ["sh", "-c", "python app/scripts/create_tables.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
