from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import OllamaLLM
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory


class FAISSChromaManager:
    def __init__(self, vectordb, hybrid_manager) -> None:
        self.vectordb = vectordb
        ## this for windows use anytherway to linux
        self.hybrid_manager = hybrid_manager
        self.llm = OllamaLLM(model="llama3.1:8b", base_url='http://ollama-container:11434')
        self.store = {}  ## Statefully manage ChatHistory
        self.conversation_chain = None
        self.faiss_index = self

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """
        Get the session_id for Chat Message History.
        """
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()

        return self.store[session_id]
    
    def update_session_history(self, session_id: str, user_message: str, bot_response: str) -> None:
        """
        Update session history with user and bot messages.
        """
        if session_id in self.store:
            history = self.store[session_id]
            history.add_user_message(user_message)
            history.add_ai_message(bot_response)
        
    def retrieve_documents(self, session_id: str, user_query: str, top_k=4):
        return self.hybrid_manager.query_hybrid_index(user_query, top_k)

    def get_retriever_chain(self, search_type="similarity"):
        """
        Get a history-aware retriever chain for searching relevant documents
        """
        # Initialize HybridEmbeddingManager with document chunks
    
        

        # Create retriever using hybrid index
        #retriever = lambda query_text, top_k=4: hybrid_manager.query_hybrid_index(query_text, top_k)

        #retriever = self.vectordb.as_retriever(search_type = search_type, search_kwargs={"k":4, 'fetch_k': 100, 'lambda_mult':1})

        contextualize_q_system_prompt = """Given a chat history and the latest user question \
                        which might reference context in the chat history, formulate a standalone question \
                        which can be understood without the chat history. Do NOT answer the question, \
                        just reformulate it if needed and otherwise return it as is."""
        
        
        # Create a prompt to generate search query based on conversation history
        # the Prompt contains the user input, the chat histroy and a message to generate a search query
        prompt_search_query = ChatPromptTemplate([
                                ("system", contextualize_q_system_prompt),
                                MessagesPlaceholder("chat_history"),
                                ("human", "{input}")
        ])
       #print("prompt_search_query: ", prompt_search_query[0])

        # Create a history-aware retriever chain
        # sends a prompts to the llm with the chat_histroy and user input to generate a search query for the retriever
        # The retreiver_chain use search query to get the relevant document from faiss(vectrorstrore) 
        # that are revelent to the user query and chat history
        history_aware_retriever  = create_history_aware_retriever(self.llm, retriever, prompt_search_query)
        return history_aware_retriever 
    
    def get_retrieved_documents_chain(self):
        """
        Get a chain for generating final responses based on retrieved documents
        """
        system_prompt = """
        You are an intelligent assistant for answer questions related tasks.\
        Use the following pieces of retrieved context to answer the quesion.\
        Your responses should be based solely on the provided company data, ensuring accuracy and relevance. \
        Use the most appropriate and relevant data from the repository to generate clear, concise, and factual answers to user queries.\
        Always search for anything requested in the query within the documents or database and provide the best possible response based on the retrieved data.\
        Make sure your answer is relevent to the quesion and it is answered from the context only.\
        Answer only in German \
        {context}
        """
        # Create a Prompt for the final response generation using retrieved documents
        # It contains the context(retrieved document from vector store), chat histroy and userinput.
        qa_prompt  = ChatPromptTemplate.from_messages([
                                ("system", system_prompt),
                                MessagesPlaceholder("chat_history"),
                                ("human","{input}"),
                                ])
        # Create a document chain to handle the retrieved documents and formulate the final answer
        # It will send the prompt to llm
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        return question_answer_chain
        
    def build_conversation_chain(self):
        """
        Build the complete conversation chain by integrating the retriever and document chains
        """
        # Call Above functions
        history_aware_retriever = self.get_retriever_chain()
        question_answer_chain = self.get_retrieved_documents_chain()

        # Create a conversation chain that integrates the retriever and document chains
        chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        # Integrate the conversation chain with session Management for history handling

        self.conversation_chain  =RunnableWithMessageHistory(
                                    chain,
                                    self.get_session_history,
                                    input_messages_key="input",
                                    history_messages_key="chat_history",
                                    output_messages_key="answer",
        )
        return self.conversation_chain

    def process_user_query(self, session_id: str, user_query: str) -> str:
        """
            Process a user query and return the bot's response.
        """
        # Retrieve chat history for the session
        history = self.get_session_history(session_id)

        # Add user query to history
        history.add_user_message(user_query)

        if not self.conversation_chain:
            self.build_conversation_chain()
        

        # Invoke the conversation chain
        response = self.conversation_chain.invoke(
            {"input": user_query},
            config={"configurable": {"session_id": session_id}}
            )
        # Extract bot response
        bot_response = response["answer"]
        # Update history with the bot's response
        self.update_session_history(session_id, user_query, bot_response)
        #print(f"Session ID: {session_id}, History: {self.get_session_history(session_id).messages}")

        return bot_response
    
    def test_search_types(self, session_id: str, user_query: str):
        """
        Test various search types with the same user query.
        """
        search_types = ["similarity", "mmr",]#, "sparse", "ann", "dense"]
        results = {}

        for search_type in search_types:
            # Create a retriever chain with the given search type
            retriever_chain = self.get_retriever_chain(search_type)
            retriever_documents = retriever_chain.invoke(
                {"input": user_query},
                config={"configurable": {"session_id": session_id}}
            )

            # Store the retrieved documents for this search type
            results[search_type] = retriever_documents

        return results

    
class HybridChainManager:
    def __init__(self, hybrid_manager, llm):
        """
        Initialize the HybridChainManager.
        Args:
            hybrid_manager: The HybridEmbeddingManager instance for hybrid retrieval.
            llm: The language model instance (e.g., OllamaLLM).
        """
        ## this for windows use anytherway to linux
        #self.llm = OllamaLLM(model="llama3.2")
        self.llm = OllamaLLM(model="llama3.1:8b", base_url='http://ollama-container:11434')
        self.store = {} ## Statefully manage ChatHistory
        self.conversation_chain = None

        self.hybrid_manager = hybrid_manager
        self.session_histories = {}  # Store chat history by session ID

    def retriever(self, query_text, top_k=4):
        """
        Retrieve documents using the hybrid manager.
        Args:
            query_text: The user's query.
            top_k: The number of top documents to retrieve.
        Returns:
            Retrieved documents as context for the response.
        """
        return self.hybrid_manager.query_hybrid_index(query_text, top_k)

    def process_user_query(self, session_id, user_query, top_k=4):
        """
        Process a user query, retrieve relevant documents, and generate a response.
        Args:
            session_id: The session ID for the chat.
            user_query: The user's query.
            top_k: The number of top documents to retrieve.
        Returns:
            The bot's response.
        """
        # Retrieve the session history
        chat_history = self.session_histories.get(session_id, [])

        # Retrieve context using the query
        retrieved_documents = self.retriever(user_query, top_k)

        # Build the system prompt with retrieved context
        system_prompt = f"""
        You are an intelligent assistant. Use the following context to answer the user's question:
        {retrieved_documents}
        Answer in German. Keep responses relevant and accurate.
        """

        # Append the retrieved documents to the chat history
        chat_history.append({"role": "system", "content": system_prompt})
        chat_history.append({"role": "user", "content": user_query})

        # Generate the bot's response
        response = self.llm.chat(chat_history)

        # Add the bot's response to the chat history
        chat_history.append({"role": "assistant", "content": response})

        # Update the session history
        self.session_histories[session_id] = chat_history

        return response
