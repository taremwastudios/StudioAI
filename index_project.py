
import os
from knowledge_manager import KnowledgeManager

def index_project(root_path: str):
    km = KnowledgeManager()
    
    # Extensions to index
    valid_exts = {'.md', '.py', '.ts', '.tsx', '.html', '.css', '.json'}
    exclude_dirs = {'.git', 'venv', '__pycache__', 'node_modules', '.gemini', 'dist', 'build', 'generated_games'}
    
    print(f"Indexing project from: {root_path}")
    
    count = 0
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext in valid_exts:
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        # Avoid indexing huge files
                        if len(content) > 100000: continue 
                        
                        rel_path = os.path.relpath(file_path, root_path)
                        km.add_entry(
                            topic=f"File: {rel_path}", 
                            content=content, 
                            tags=ext, 
                            source=rel_path
                        )
                        count += 1
                        print(f"Indexed: {rel_path}")
                except Exception as e:
                    print(f"Failed to index {f}: {e}")
                    
    print(f"Indexing complete. Added {count} files to Knowledge Base.")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    index_project(project_root)
