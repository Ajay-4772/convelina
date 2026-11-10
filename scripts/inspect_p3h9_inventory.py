import sys
import os
import json
sys.path.insert(0, "backend")

print("Importing app.main...", flush=True)
from app.main import app
print("Imported app.main successfully", flush=True)

def get_all_dependencies(dependant):
    deps = []
    if dependant.call and hasattr(dependant.call, "__name__"):
        deps.append(dependant.call.__name__)
    for sub in dependant.dependencies:
        deps.extend(get_all_dependencies(sub))
    return deps

routes = []
for r in app.routes:
    if hasattr(r, "methods"):
        methods = sorted(list(r.methods))
        path = r.path
        endpoint = r.endpoint.__name__
        doc = (r.endpoint.__doc__ or "").strip().split("\n")[0]
        
        deps = []
        if hasattr(r, "dependant"):
            deps = get_all_dependencies(r.dependant)
        
        dep_names_lower = [d.lower() for d in deps]
        
        role_req = "PUBLIC"
        if any("admin" in d for d in dep_names_lower) or "/admin" in path:
            role_req = "ADMIN"
        elif any("current_user" in d or "require_current" in d or "get_current" in d for d in dep_names_lower):
            role_req = "USER"
        elif path.startswith("/api/v1/documents") or path.startswith("/api/v1/conflicts") or path.startswith("/api/v1/conversations") or path.startswith("/api/v1/correction-drafts"):
            role_req = "USER"

        routes.append({
            "methods": methods,
            "path": path,
            "endpoint": endpoint,
            "summary": doc,
            "dependencies": sorted(list(set(deps))),
            "role_requirement": role_req
        })

routes.sort(key=lambda x: (x["role_requirement"], x["path"]))

print(f"Total API Routes: {len(routes)}")
role_counts = {}
for r in routes:
    role_counts[r["role_requirement"]] = role_counts.get(r["role_requirement"], 0) + 1
print(f"Breakdown by role requirement: {role_counts}")

output_path = "scripts/p3h9_api_routes.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(routes, f, indent=2)
print(f"Saved route inventory to {output_path}")
