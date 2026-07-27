import time
import logging
from django.db import connection, reset_queries

logger = logging.getLogger(__name__)

class QueryCountProfiler:
    """
    Gestionnaire de contexte pour profiler et compter le nombre de requêtes SQL
    exécutées lors de l'exécution d'un bloc de code (Détective N+1).
    """
    def __init__(self, name: str = "Bloc"):
        self.name = name
        self.initial_queries = 0
        self.final_queries = 0
        self.start_time = 0.0
        self.execution_time = 0.0

    def __enter__(self):
        reset_queries()
        self.initial_queries = len(connection.queries)
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.execution_time = time.time() - self.start_time
        self.final_queries = len(connection.queries)
        query_count = self.final_queries - self.initial_queries
        
        logger.info(f"[PROFILER] {self.name} - Requêtes SQL: {query_count} | Temps: {self.execution_time:.4f}s")
        if query_count > 10:
            logger.warning(f"[PROFILER WARNING] {self.name} a exécuté {query_count} requêtes SQL (Risque potentiel de N+1).")
