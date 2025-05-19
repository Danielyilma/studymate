from ai_tools.faiss_loader import SessionVectorStore

class VectorStoreSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SessionVectorStore()
        return cls._instance