import os
import sqlite3
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer


class DataModel:
    def __init__(self, sqlite_path: str, vector_cfg: dict):
        # SQLite
        self.conn = sqlite3.connect(sqlite_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Qdrant
        self.qdrant_client = QdrantClient(url=vector_cfg["url"], api_key=vector_cfg["api_key"])
        self.vector_model = SentenceTransformer("all-MiniLM-L6-v2")

        # Internal doc structure
        self.documentation = {"structured": {}, "unstructured": {}}

    def fetch_tables(self, whitelist: Optional[List[str]] = None) -> List[str]:
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        print(self.cursor.fetchall())
        tables = [row["name"] for row in self.cursor.fetchall()]
        print(tables)
        if whitelist:
            tables = [t for t in tables if t in whitelist]
        return tables

    def fetch_or_init_table_doc(self, table_name: str):
        doc_table = f"_{table_name}"
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (doc_table,)
        )
        exists = self.cursor.fetchone()

        if not exists:
            self.create_doc_table(table_name)
            self.documentation["structured"][table_name] = {}
        else:
            self.cursor.execute(f"SELECT * FROM {doc_table}")
            rows = self.cursor.fetchall()
            self.documentation["structured"][table_name] = {
                row["column_name"]: row["description"] for row in rows
            }

    def create_doc_table(self, table_name: str):
        doc_table = f"_{table_name}"
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {doc_table} (
                column_name TEXT PRIMARY KEY,
                description TEXT
            );
        """)
        self.conn.commit()
        print(f"✅ Created doc table '{doc_table}'")

    def update_table_doc(self, table_name: str, column_docs: Dict[str, str]):
        doc_table = f"_{table_name}"
        for column, desc in column_docs.items():
            self.cursor.execute(f"""
                INSERT INTO {doc_table} (column_name, description)
                VALUES (?, ?)
                ON CONFLICT(column_name) DO UPDATE SET description=excluded.description
            """, (column, desc))
        self.conn.commit()
        self.documentation["structured"][table_name] = column_docs
        print(f"✅ Updated documentation for '{table_name}'")

    def fetch_unstructured_collections(self, whitelist: Optional[List[str]] = None):
        collections = self.qdrant_client.get_collections().collections
        names = [col.name for col in collections]
        return [n for n in names if not whitelist or n in whitelist]

    def add_unstructured_doc(self, collection_name: str, description: str, update_db: bool = False):
        if update_db:
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_model.get_sentence_embedding_dimension(),
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Created collection '{collection_name}'")

        self.documentation["unstructured"][collection_name] = description
        print(f"📝 Updated documentation for collection '{collection_name}'")

    def get_documentation_dict(self):
        return self.documentation

    def close(self):
        self.conn.close()
