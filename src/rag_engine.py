import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
import os

class RAGEngine:
    def __init__(self, persist_directory: str = "./chroma_db"):
        # Create directory if not exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Use sentence transformers for embeddings
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create Chroma client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collection for guide text
        self.collection_name = "successfactors_guide"
        self.collection = None
    
    def create_collection(self):
        """Create or get existing collection"""
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn
            )
            print(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn
            )
            print(f"Created new collection: {self.collection_name}")
    
    def index_guide_pages(self, pages: List[Dict[str, Any]]):
        """Index guide pages in vector database"""
        print(f"Indexing {len(pages)} pages...")
        
        documents = []
        metadatas = []
        ids = []
        
        for page in pages:
            page_num = page["page_number"]
            text = page["text"]
            
            # Skip empty pages
            if len(text.strip()) < 10:
                continue
            
            documents.append(text)
            metadatas.append({
                "page": page_num,
                "has_images": len(page.get("images", [])) > 0
            })
            ids.append(f"page_{page_num}")
        
        # Add to collection
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Indexed {len(documents)} pages")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant guide pages"""
        if not self.collection:
            self.create_collection()
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "page": results['metadatas'][0][i]['page'],
                    "text": results['documents'][0][i],
                    "has_images": results['metadatas'][0][i]['has_images']
                })
        
        return formatted_results