import sys
try:
    import app.routers.documents
    import app.routers.knowledge
    import app.rag.assistant.orchestrator
    import app.rag.generation.llm_provider
    import app.core.synthetic_documents
    print("ALL_IMPORTS_PASSED")
except Exception as e:
    print(f"IMPORT_ERROR: {e}")
    sys.exit(1)
