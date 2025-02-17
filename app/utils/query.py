

# Function for rewriting a query to improve retrieval
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.prompts import PromptTemplate
from sklearn.metrics.pairwise import cosine_similarity
from IPython.display import display, Markdown


def rewrite_query(original_query, llm_chain):
    """
    Rewrite the original query to improve retrieval.

    Args:
    original_query (str): The original user query
    llm_chain: The chain used to generate the rewritten query

    Returns:
    str: The rewritten query
    """
    response = llm_chain.invoke(original_query)
    return response


# Function for generating a step-back query to retrieve broader context
def generate_step_back_query(original_query, llm_chain):
    """
    Generate a step-back query to retrieve broader context.

    Args:
    original_query (str): The original user query
    llm_chain: The chain used to generate the step-back query

    Returns:
    str: The step-back query
    """
    response = llm_chain.invoke(original_query)
    return response


# Function for decomposing a query into simpler sub-queries
def decompose_query(original_query, llm_chain):
    """
    Decompose the original query into simpler sub-queries.

    Args:
    original_query (str): The original complex query
    llm_chain: The chain used to generate sub-queries

    Returns:
    List[str]: A list of simpler sub-queries
    """
    response = llm_chain.invoke(original_query)
    sub_queries = [q.strip() for q in response.split('\n') if q.strip() and not q.strip().startswith('Sub-queries:')]
    return sub_queries

def HyDE(original_query, llm_chain):
    """

    """
    response = llm_chain.invoke(original_query)
    return response


class RAGQueryProcessor:
    def __init__(self):

        self.llm = OllamaLLM(model="llama3.1:8b", base_url='http://ollama-container:11434')
        self.embed_model = OllamaEmbeddings(model='nomic-embed-text', base_url="http://ollama-container:11434")
        # Initialize LLM models
        self.re_write_llm = self.llm
        self.step_back_llm = self.llm
        self.sub_query_llm = self.llm
        self.hyde_llm = self.llm

        # Initialize prompt templates
        query_rewrite_template = """You are an AI assistant tasked with reformulating user queries to improve retrieval in a RAG system. 
        Given the original query, rewrite it to be more specific, detailed, and likely to retrieve relevant information.

        Original query: {original_query}

        Rewritten query:"""

        step_back_template = """You are an AI assistant tasked with generating broader, more general queries to improve context retrieval in a RAG system.
        Given the original query, generate a step-back query that is more general and can help retrieve relevant background information.

        Original query: {original_query}

        Step-back query:"""
        subquery_decomposition_template = """You are an AI assistant tasked with breaking down complex queries into simpler sub-queries for a RAG system.
        Given the original query, decompose it into 2-4 simpler sub-queries that, when answered together, would provide a comprehensive response to the original query.

        Original query: {original_query}

        example: What are the impacts of climate change on the environment?

        Sub-queries:
        1. What are the impacts of climate change on biodiversity?
        2. How does climate change affect the oceans?
        3. What are the effects of climate change on agriculture?
        4. What are the impacts of climate change on human health?"""

        HyDE_tempelte = """You are an expert at using a quesion to generate a document useful for answering the question.
        Given a question, generate a paragraph of the text that answers the question.
        start direct with answer.
        Original query: {original_query}"""

        # Create LLMChains
        self.query_rewriter = PromptTemplate(input_variables=["original_query"],
                                             template=query_rewrite_template) | self.re_write_llm
        self.step_back_chain = PromptTemplate(input_variables=["original_query"],
                                              template=step_back_template) | self.step_back_llm
        self.subquery_decomposer_chain = PromptTemplate(input_variables=["original_query"],
                                                        template=subquery_decomposition_template) | self.sub_query_llm
        self.query_rewriter = PromptTemplate(input_variables=["original_query"],
                                             template=query_rewrite_template) | self.re_write_llm
        self.hyde_chain = PromptTemplate(input_variables=["original_query"],
                                         template=HyDE_tempelte) | self.hyde_llm
        self.actual_document = """ Climate change significantly impacts the environment, causing widespread and interconnected effects.
        Rising global temperatures lead to the melting of polar ice caps and glaciers, contributing to sea level rise and threatening coastal e
        cosystems and communities. Shifts in weather patterns result in more frequent and intense extreme events, such as hurricanes, droughts, an
        d heatwaves, which disrupt ecosystems and human livelihoods. Warmer temperatures also alter habitats, pushing many species to migrate or face 
        extinction if they cannot adapt. Coral reefs, crucial for marine biodiversity, are dying due to ocean warming and acidification. Additionally, 
        deforestation and desertification are exacerbated as a result of changing rainfall patterns and prolonged droughts, reducing the planet's capacity
        to absorb carbon dioxide and worsening climate change further. These environmental changes not only threaten biodiversity but also compromise critical 
        resources like water, food, and air quality, posing challenges for the planet's health and human survival. """
        
    def run(self, original_query):
        """
        Run the full RAG query processing pipeline.

        Args:
        original_query (str): The original query to be processed
        """
        # Rewrite the query
        rewritten_query = rewrite_query(original_query, self.query_rewriter)
        print("Original query:", original_query)
        # print("\nRewritten query:", rewritten_query)
        display(Markdown(f"**Rewritten query:**\n\n{rewritten_query}"))
        print("\n----------------------------------------------------------------")

        # Generate step-back query
        step_back_query = generate_step_back_query(original_query, self.step_back_chain)
        # print("\nStep-back query:", step_back_query)
        display(Markdown(f"**Step-back query:**\n\n{step_back_query}"))
        print("\n----------------------------------------------------------------")

        # Decompose the query into sub-queries
        sub_queries = decompose_query(original_query, self.subquery_decomposer_chain)
        print("\nSub-queries:")
        for i, sub_query in enumerate(sub_queries, 1):
            display(Markdown(f"{sub_query}"))
        print("\n----------------------------------------------------------------")

        # Rewrite the query
        hydy_document = HyDE(original_query, self.hyde_chain)

        # print("\nHypothetical document:", hydy_document)
        display(Markdown(f"**Hypothetical document:**\n\n{hydy_document}"))
        print("\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        question_embeddings = self.embed_model.embed_documents([original_query])
        hypothetical_document_emb = self.embed_model.embed_documents([hydy_document])
        actual_document_emb = self.embed_model.embed_documents([self.actual_document])
        print(f"similarity without HyDE:  {cosine_similarity(question_embeddings, actual_document_emb)}")
        print(f"similarity with HyDE:  {cosine_similarity(hypothetical_document_emb, actual_document_emb)}")
        print("\n----------------------------------------------------------------")
