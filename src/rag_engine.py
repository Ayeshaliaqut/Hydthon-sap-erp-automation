import chromadb
from chromadb.config import Settings
from typing import List, Dict

class RAGEngine:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = None
    
    def create_collection(self):
        """Create tasks collection"""
        try:
            self.collection = self.client.get_collection(name="tasks")
        except:
            self.collection = self.client.create_collection(name="tasks")
    
    def index_tasks(self, tasks: List[Dict]):
        """Index tasks with metadata"""
        print(f"Indexing {len(tasks)} tasks...")
        
        documents = []
        metadatas = []
        ids = []
        
        for task in tasks:
            documents.append(task["text"])
            metadatas.append({
                "task_number": task["task_number"],
                "page": task["page"],
                "has_steps": task["has_steps"],
                "step_count": task["step_count"]
            })
            ids.append(task["id"])
        
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Indexed {len(documents)} tasks")
    
    def search_tasks(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search tasks"""
        if not self.collection:
            self.create_collection()
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted = []
        if results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted.append({
                    "task_id": results['ids'][0][i],
                    "task_number": results['metadatas'][0][i]['task_number'],
                    "page": results['metadatas'][0][i]['page'],
                    "text": results['documents'][0][i],
                    "has_steps": results['metadatas'][0][i]['has_steps'],
                    "step_count": results['metadatas'][0][i]['step_count']
                })
        
        return formatted