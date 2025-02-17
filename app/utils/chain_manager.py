from typing import AsyncIterable
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import OllamaLLM, ChatOllama
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
import logging
from fastapi import Depends
from sqlalchemy.orm import Session
from app.models.models import ChatHistory
from app.database.config import get_db
from app.database.helper_insert_update_chathistory import insert_user_question, update_assistant_answer
from app.models.models import ChatHistory
from app.utils.advanced_vector_retriever import AdvancedVectorRetriever
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager   
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

class ConversationalChainManager:

    def __init__(self, llm_name = 'llama3.1:8b') -> None:
        #self.vectordb = vectordb
        self.base_url = 'http://ollama-container:11434'
        ## this for windows use anytherway to linux
        self.llm_name = llm_name
        #mode_name = "deepseek-r1:32b" or "llama3.1:8b"
        self.llm_chat = ChatOllama(model=self.llm_name, base_url=self.base_url)# 
        self.llm = OllamaLLM(model=self.llm_name, base_url=self.base_url)
        self.store = {} ## Statefully manage ChatHistory
        self.conversation_chain = None
        # self.retriever = self.vectordb.as_retriever(search_type = "similarity", search_kwargs={"k":4, 'fetch_k': 100, 'lambda_mult':1})

    # def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
    #     """
    #     Get the session_id for Chat Message History.
    #     """
    #     if session_id not in self.store:
    #         self.store[session_id] = ChatMessageHistory()
    #         logging.info(f"Created new chat history for session_id: {session_id}")
    #     else:
    #         logging.info(f"Using existing chat history for session_id: {session_id}")

    #     # Log the current history
    #     history = self.store[session_id]
    #     logging.info(f"Current history for session {session_id}: {history.messages}")
    
    #     return history
    
    # def update_session_history(self, session_id: str, user_message: str, bot_response: str) -> None:
    #     """
    #     Update session history with user and bot messages.
    #     """
    #     if session_id in self.store:
    #         history = self.store[session_id]
    #         history.add_user_message(user_message)
    #         history.add_ai_message(bot_response)
    #         logging.info(f"Updated history for session {session_id} with user message: {user_message} and bot response: {bot_response}")

    def load_session_history(self, session_id, )->BaseChatMessageHistory:
        chat_history  = ChatMessageHistory()
        db = next(get_db())
        try:

            session = db.query(ChatHistory).filter(ChatHistory.session_id == session_id).all()
            if session:
                for record in session:
                    if record.question:
                        chat_history.add_user_message(record.question)
                    if record.response:    
                        chat_history.add_ai_message(record.response)
            return chat_history
        except Exception as e:  
            print(f"An unexpected error occurred: {e}")
            return {}

    def get_session_history(self, session_id:str) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = self.load_session_history(session_id)

        return self.store[session_id]


    def get_retriever_chain(self, retriever): #search_type="similarity"):
        """
        Get a history-aware retriever chain for searching relevant documents
        """
        #retriever_instance = AdvancedVectorRetriever(self.vectordb)
        #retriever = retriever_instance.retrieve_documents(search_type=search_type)
        # retriever = self.vectordb.as_retriever(search_type = search_type, search_kwargs={"k":4, 'fetch_k': 100, 'lambda_mult':1})

        contextualize_q_system_prompt = """Given a chat history and the latest user question \
                        which might reference context in the chat history, formulate a standalone question \
                        which can be understood without the chat history.\
                        if current query is not relevent to previous History then dont use chat history. \
                        Do NOT answer the question, just reformulate it if needed and otherwise return it as is.\
                        """
        
        
        # Create a prompt to generate search query based on conversation history
        # the Prompt contains the user input, the chat histroy and a message to generate a search query
        prompt_search_query = ChatPromptTemplate.from_messages([
                                ("system", contextualize_q_system_prompt),
                                MessagesPlaceholder(variable_name= "chat_history"),
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
        Use the most appropriate and relevant data from the repository to generate clear, concise, and factual answers to user queries.\
        Always search for anything requested in the query within the documents or database and provide the best possible response based on the retrieved data.\
        Make sure your answer is relevent to the quesion and it is answered from the context only.\
        Use markdown styling to form your answers if required. Ensure the markdown is valid and well-formatted.\
        Answer only in German if user ask to translate in other language then translate it otherwise only answer in German. \
        if user ask about age or somthing like that then current year is 2025 Feb. \
        At the end give always the header or title or source of your answer\
        {context}
        """
        # Create a Prompt for the final response generation using retrieved documents
        # It contains the context(retrieved document from vector store), chat histroy and userinput.
        qa_prompt  = ChatPromptTemplate.from_messages([
                                ("system", system_prompt),
                                MessagesPlaceholder(variable_name="chat_history"),
                                ("human","{input}"),
                                ])
        # Create a document chain to handle the retrieved documents and formulate the final answer
        # It will send the prompt to llm
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        return question_answer_chain
        
    def build_conversation_chain(self, retriever):
        """
        Build the complete conversation chain by integrating the retriever and document chains
        """
        # Call Above functions
        history_aware_retriever = self.get_retriever_chain(retriever)
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
            Process a user query and stream the bot's response token-by-token.
        """
        logging.info(f"Processing user query for session {session_id}: {user_query}")
        
        # # Rewrite the query
        #rewritten_query, formatted_prompt, formatted_history = self.rewrite_query(session_id, user_query)
        #print("updated query: ", rewritten_query)

        # Retrieve chat history for the session
        history = self.get_session_history(session_id)
        logging.info(f"History: {history}")

        if not self.conversation_chain:
            self.build_conversation_chain()
        
        # Invoke the conversation chain
        response = self.conversation_chain.invoke(
            {"input": user_query},
            config={"configurable": {"session_id": session_id}})
        #Extract bot response
        #print("response: ", response)
        bot_response = response["answer"]
        #update_assistant_answer(chat_id, bot_response, db=db)
        # Update history with the bot's response
        #self.update_session_history(session_id, rewritten_query, bot_response)
        #print(f"Session ID: {session_id}, History: {self.get_session_history(session_id).messages}")

        return bot_response
    
    def rewrite_query(self, session_id: str, user_query: str):
        """
        Rewrite the user query based on the chat history.
        """

        
        history = self.get_session_history(session_id)
        logging.info(f"History: {history}")


        # Define the prompt for query rewriting
        rewrite_prompt = """
        Given the following conversation history and latest original query, generate a step-back query that is more general, clear, precise and \
        to be more relevant to the conversation, which can help retrieve relevant background information. \
        If the latest user input is not directly related to the conversation history, rewrite it to be more specific, and likely \
        to retrieve relevant information. \
        Do not answer the question, just rewrite it if needed and otherwise return it as is. \
        Conversation History: {history} \
        User Input: {user_input} \
        Step-back query:
        """ 
            
        # Format the chat history as a single string
        formatted_history = "\n".join(
            [f"Human: {msg.content}" if msg.type == "human" else f"AI: {msg.content}" for msg in history.messages]
        )
        logging.info(f"Formatted History: {formatted_history}")
        logging.info(f"-----------------------------------------------")

        # Format the input prompt as a string
        formatted_prompt = rewrite_prompt.format(history=formatted_history, user_input=user_query)
        # Log the formatted prompt for debugging purposes
        logging.info(f"Formatted Prompt: {formatted_prompt}")
        logging.info(f"-----------------------------------------------")

        # Use the LLM to rewrite the query
        rewritten_query = self.llm.invoke(formatted_prompt)
        return rewritten_query.strip(), formatted_prompt, formatted_history
            
    
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

    # def hybrid_search(self, chunks, query):
    #     retriever_vectordb = self.vectordb.as_retriever(search_kwargs={"k": 5})
    #     keyword_retriever = BM25Retriever.from_documents(chunks, search_kwargs={"k": 5})
    #     ensemble_retriever = EnsembleRetriever(retrievers = [retriever_vectordb, keyword_retriever], weights=[0.5, 0.5])

    #     compressed_docs = ensemble_retriever.invoke(query)
    #     return compressed_docs