import os
import re
import json
from typing import List, Dict, Any

class ProjectAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.workspace_dir = os.path.join(root_dir, "projects")
        self.ignore_dirs = {".git", "node_modules", "venv", "__pycache__", "build", "dist"}
        self.supported_exts = {".gd", ".cs", ".py", ".ts", ".tsx", ".html", ".css", ".json", ".tscn", ".tres", ".godot"} # Added Godot-specific file types

    def scan_project(self) -> List[Dict[str, Any]]:
        target_dir = self.workspace_dir if os.path.exists(self.workspace_dir) else self.root_dir
        
        ai_managed_projects: List[Dict[str, Any]] = []

        # Iterate through subdirectories in the target_dir to find individual projects
        for project_name in os.listdir(target_dir):
            project_path = os.path.join(target_dir, project_name)
            if not os.path.isdir(project_path):
                continue
            
            project_report = {
                "name": project_name,
                "path": os.path.relpath(project_path, self.root_dir),
                "is_ai_managed": False,
                "manifest": {},
                "todos": [],
                "potential_issues": [],
                "files_overview": {}
            }

            manifest_path = os.path.join(project_path, ".studio_manifest")
            if os.path.exists(manifest_path):
                project_report["is_ai_managed"] = True
                try:
                    with open(manifest_path, 'r') as f:
                        project_report["manifest"] = json.load(f)
                except json.JSONDecodeError:
                    project_report["potential_issues"].append({"type": "Error", "message": f"Malformed .studio_manifest in {project_name}"})
            
            # If it's an AI-managed project or a Godot project, scan its files
            if project_report["is_ai_managed"] or os.path.exists(os.path.join(project_path, "project.godot")):
                for root, dirs, files in os.walk(project_path):
                    dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
                    
                    for file in files:
                        ext = os.path.splitext(file)[1]
                        if ext in self.supported_exts:
                            path = os.path.join(root, file)
                            rel_path_in_project = os.path.relpath(path, project_path)
                            project_report["files_overview"][rel_path_in_project] = {"size": os.path.getsize(path), "ext": ext}
                            
                            try:
                                with open(path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    lines = content.splitlines()
                                    
                                    for i, line in enumerate(lines):
                                        if any(kw in line.upper() for kw in ["TODO:", "FIXME:"]):
                                            project_report["todos"].append({"file": rel_path_in_project, "line": i+1, "text": line.strip()})
                                    
                                    # Godot-specific styling check (GDScript)
                                    if ext == ".gd":
                                        if re.search(r"^\s*func\s+_\w+_\w+\s*\(", content, re.MULTILINE) and not re.search(r"^\s*#\s*pragma\s+once", content, re.MULTILINE):
                                            project_report["potential_issues"].append({
                                                "file": rel_path_in_project, "type": "Godot Convention", "message": "GDScript method uses _snake_case, consider standard Godot naming or add '# pragma once'"
                                            })
                                        if "var " in content and ":" not in content:
                                            project_report["potential_issues"].append({
                                                "file": rel_path_in_project, "type": "Styling", "message": "Missing Static Typing in GDScript"
                                            })
                            except Exception as e:
                                project_report["potential_issues"].append({
                                    "file": rel_path_in_project, "type": "Error", "message": f"Could not read file: {e}"
                                })
            
            if project_report["is_ai_managed"] or project_report["todos"] or project_report["potential_issues"] or project_report["files_overview"]:
                ai_managed_projects.append(project_report)
        
        return ai_managed_projects

analyzer = ProjectAnalyzer("/home/Taremwastudios/TaremwaStudios") # Scan from the root to find 'projects'