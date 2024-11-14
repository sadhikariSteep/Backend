import glob, os
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

#-------------------------------------------------------------------------------#
#                           TODO                                                #
# conversion from diffent document format like docx, pdf, which contain...      #
# so that please check the converted pain text contain txt in their oder        # 
#                                                                               #
#                                                                               #
#-------------------------------------------------------------------------------#

class DocumentManager:
    """ Load the document from user defined location and split it into smaller chunks so that it can easily process"""
    def __init__(self, directory_path, glob_pattern=("*.pdf","*.docx","*.txt")):
        self.directory_path = directory_path
        self.glob_pattern = glob_pattern
        self.documents = []
        self.chunks = []

    def load_documents(self):
        """ Load the documents form the list of file path."""
        for pattern in self.glob_pattern:

            documents_path = glob.glob(os.path.join(self.directory_path, pattern))
            # print("path..: ", documents_path)
            for document_path in documents_path:
                # Check for pdf and load it
                if document_path.endswith('.pdf'):
                    document_loader = PyPDFLoader(document_path)
                # Check for docx and load it
                elif document_path.endswith('.docx'):
                    document_loader = Docx2txtLoader(document_path)
                # Check for txt and load it
                elif document_path.endwith('.txt'):
                    document_loader = TextLoader(document_path)
                #other cases asked user to check the document format.
                else:
                    print(f'Please check documets format.')

                # Extend the documents list with loaded content
                self.documents.extend(document_loader.load())

        return self.documents

    def split_document(self, documents=None):
        """Split a list of documents into Chunks."""
        if documents is None:
            # Load the documents if they havenot been loaded yet
            if not self.documents:
                self.load_documents()
            # Load the document where they saved
            documents = self.documents
        # Check documents
        if not documents:
            raise ValueError("No documents to split. Please check the documents first.")
        
        # split mehtod
        # we can test here other splitter
        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=1500,
                            chunk_overlap=100,
                            length_function=len,
                            is_separator_regex=False
                            )
        self.chunks = text_splitter.split_documents(documents)
        return self.chunks