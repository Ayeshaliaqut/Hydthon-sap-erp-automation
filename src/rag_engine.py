# rag_engine.py

import chromadb
from chromadb.config import Settings
from typing import List, Dict
import json

class RAGEngine:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = None
        self.setup_collection()
    
    def setup_collection(self):
        """Create or get the tasks collection"""
        try:
            self.collection = self.client.get_collection(name="support_tasks")
        except:
            self.collection = self.client.create_collection(
                name="support_tasks",
                metadata={"hnsw:space": "cosine"}
            )
    
    def index_tasks(self, tasks: List[Dict]):
        """Index tasks for semantic search"""
        print(f"\n📚 Indexing {len(tasks)} tasks in RAG...")
        
        documents = []
        metadatas = []
        ids = []
        
        for task in tasks:
            # Create rich searchable text
            searchable_text = f"""
            Task {task['task_number']}: {task.get('title', '')}
            {task['text']}
            
            Steps:
            {self._format_steps_for_search(task.get('steps', []))}
            """
            
            documents.append(searchable_text)
            
            # Store metadata for retrieval
            metadatas.append({
                "task_number": str(task['task_number']),
                "title": task.get('title', ''),
                "step_count": str(task['step_count']),
                "image_count": str(task.get('image_count', 0)),
                "pages": json.dumps(task.get('pages', [])),
                "steps_json": json.dumps(task.get('steps', [])),
                "has_steps": str(task['has_steps'])
            })
            
            ids.append(task['id'])
        
        # Clear existing collection and reindex
        try:
            self.client.delete_collection("support_tasks")
        except:
            pass
        
        self.setup_collection()
        
        # Add in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            self.collection.add(
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )
        
        print(f"✅ Indexed {len(tasks)} tasks successfully")
    
    def _format_steps_for_search(self, steps: List[Dict]) -> str:
        """Format steps to be searchable"""
        if not steps:
            return "No steps"
        
        step_texts = []
        for step in steps[:5]:
            step_texts.append(f"{step['step']}. {step['instruction']} ({step['type']})")
        
        return "\n".join(step_texts)
    
    def search_tasks(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search for relevant tasks"""
        if not self.collection:
            self.setup_collection()
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["metadatas", "distances"]
            )
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
        
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                # Parse metadata
                metadata = results['metadatas'][0][i]
                
                # Parse steps
                steps = []
                if metadata.get('steps_json'):
                    try:
                        steps = json.loads(metadata['steps_json'])
                    except:
                        steps = []
                
                # Parse pages
                pages = []
                if metadata.get('pages'):
                    try:
                        pages = json.loads(metadata['pages'])
                    except:
                        pages = []
                
                # Calculate relevance (lower distance = more relevant)
                relevance = 1.0
                if results.get('distances'):
                    relevance = 1.0 - (results['distances'][0][i] / 2)  # Normalize to 0-1
                
                formatted_results.append({
                    "task_id": results['ids'][0][i],
                    "task_number": metadata.get('task_number', '0'),
                    "title": metadata.get('title', ''),
                    "step_count": int(metadata.get('step_count', 0)),
                    "image_count": int(metadata.get('image_count', 0)),
                    "pages": pages,
                    "steps": steps,
                    "has_steps": metadata.get('has_steps') == 'True',
                    "relevance_score": round(relevance, 3)
                })
        
        # Sort by relevance
        formatted_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return formatted_results
    
    def delete_collection(self):
        """Reset the collection"""
        try:
            self.client.delete_collection("support_tasks")
            print("🗑️ Collection deleted")
            self.collection = None
        except:
            pass