#!/bin/bash
# Start the Ollama service
./bin/ollama serve &
# # Pull the model if it's not already downloaded
# if [ ! -d "/root/.ollama/llama3.1:8b" ]; then
#   sleep 5
#   echo "Pulling llama3.1:8b model..."
#   ollama pull llama3.1:8b
# else
#   echo "Model already downloaded."
# fi
pid=$!

sleep 5

echo "Pulling llama3 model"
ollama pull llama3.1:8b
wait $pid