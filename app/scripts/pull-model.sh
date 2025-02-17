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

echo ".......................Pulling llama3.2:3b model..............."
ollama pull llama3.2:3b

echo ".......................Pulling llama3.1:8b model..............."
ollama pull llama3.1:8b

#echo ".......................Pulling llama3.3 model..............."
#ollama pull llama3.3

echo ".......................pulling deepseek-r1:32b model..............."
ollama pull deepseek-r1:32b

echo ".......................pulling deepseek-r1:8b model..............."
ollama pull deepseek-r1:8b

echo ".......................Pulling embedding model..........."
ollama pull nomic-embed-text

echo ".......................bge-m3..........."
ollama pull bge-m3

echo ".......................bge-large..........."
ollama pull bge-large

echo ".......................jina-embeddings-v2-base-de..........."
ollama pull jina/jina-embeddings-v2-base-de
wait $pid