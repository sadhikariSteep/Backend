from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import OllamaLLM
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory


class ConversationalChainManager:

    def __init__(self, vectordb) -> None:
        self.vectordb = vectordb


        ## this for windows use anytherway to linux
        #self.llm = OllamaLLM(model="llama3.2")
        self.llm = OllamaLLM(model="llama3.1:8b", base_url='http://ollama-container:11434')
        self.store = {} ## Statefully manage ChatHistory
        self.conversation_chain = None

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """
        Get the session_id for Chat Message History.
        """
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()

        return self.store[session_id]

    def get_retriever_chain(self):
        """
        Get a history-aware retriever chain for searching relevant documents
        """
        retriever = self.vectordb.as_retriever(search_kwargs={"k":4})

        contextualize_q_system_prompt = """Given a chat history and the latest user question \
                        which might reference context in the chat history, formulate a standalone question \
                        which can be understood without the chat history. Do NOT answer the question, \
                        just reformulate it if needed and otherwise return it as is."""
        
        
        # Create a prompt to generate search query based on conversation history
        # the Prompt contains the user input, the chat histroy and a message to generate a search query
        prompt_search_query = ChatPromptTemplate.from_messages([
                                ("system", contextualize_q_system_prompt),
                                MessagesPlaceholder("chat_history"),
                                ("user", "{input}")
        ])

        # Create a history-aware retriever chain
        # sends a prompts to the llm with the chat_histroy and user input to generate a search query for the retriever
        # The retreiver_chain use search query to get the relevant document from faiss(vectrorstrore) 
        # that are revelent to the user query and chat history
        retriever_chain = create_history_aware_retriever(self.llm, retriever, prompt_search_query)
        return retriever_chain
    
    def get_retrieved_documents_chain(self):
        """
        Get a chain for generating final responses based on retrieved documents
        """
        system_prompt = """You are an assistant designed to provide company-specific internal information and reply in german.\
                        You will be given queries related to company data and other internal resources which is steep Training Referenzen.\
                        Answer the questions accurately using the provided information. If the information is not available or \
                        you are unsure, respond with 'I do not have that information.' \
                        Do not speculate or provide information outside the company's data scope.\
                        {context}"""
        # Create a Prompt for the final response generation using retrieved documents
        # It contains the context(retrieved document from vector store), chat histroy and userinput.
        prompt_get_answer = ChatPromptTemplate.from_messages([
                                ("system", system_prompt),
                                MessagesPlaceholder("chat_history"),
                                ("user","{input}"),
                                ])
        # Create a document chain to handle the retrieved documents and formulate the final answer
        # It will send the prompt to llm
        documents_chain = create_stuff_documents_chain(self.llm, prompt_get_answer)
        return documents_chain
        
    def build_conversation_chain(self):
        """
        Build the complete conversation chain by integrating the retriever and document chains
        """
        # Call Above functions
        retriever_chain = self.get_retriever_chain()
        documents_chain = self.get_retrieved_documents_chain()

        # Create a conversation chain that integrates the retriever and document chains
        chain = create_retrieval_chain(retriever_chain, documents_chain)
        
        # Integrate the conversation chain with session Management for history handling

        self.conversation_chain  =RunnableWithMessageHistory(
                                    chain,
                                    self.get_session_history,
                                    input_messages_key="input",
                                    history_messages_key="chat_history",
                                    output_messages_key="answer",
        )
        return self.conversation_chain

    def run_conversation(self, user_question):
        """
            Run the conversation chain with the given user input.
        """

        if not self.conversation_chain:
            raise ValueError("Conversation chain not initialized. Call 'build_conversation_chain' first.")
    
        return self.conversational_chain.invoke({"input":user_question},
                                                config={"configurable": {"session_id": "abc123"}}, 
                                                )