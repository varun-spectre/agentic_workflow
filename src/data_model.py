import os
import json
import requests
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer


class DataModel:
    def __init__(self, structured_cfg, vector_cfg, schema="public"):
        # Structured DB config (Supabase)
        self.supabase_url = structured_cfg["SUPABASE_URL"]
        self.api_key = structured_cfg["SUPABASE_API_KEY"]
        self.schema = schema
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Vector DB config (Qdrant)
        self.qdrant_client = QdrantClient(url=vector_cfg["url"], api_key=vector_cfg["api_key"])
        self.vector_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Internal state
        self.documentation = {"structured": {}, "unstructured": {}}

    def fetch_tables(self, whitelist: Optional[List[str]] = None):
        sql = """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name NOT LIKE '_%';
        """

        url = f"{self.supabase_url}/rest/v1/rpc/execute_sql"
        response = requests.post(url, headers=self.headers, json={"query": sql})

        if response.status_code != 200 or not response.content.strip():
            print("⚠️ Failed to fetch table list or got empty result.")
            return []

        try:
            result = response.json()
            tables = [row["table_name"] for row in result]
            if whitelist:
                tables = [t for t in tables if t in whitelist]
            return tables
        except json.JSONDecodeError:
            print("❌ JSON decoding failed. Response was:")
            print(response.text)
            return []





    def fetch_or_init_table_doc(self, table_name: str):
        doc_table_name = f"_{table_name}"
        url = f"{self.supabase_url}/rest/v1/{doc_table_name}?select=*"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 404:
            print(f"⚠️ Documentation table '{doc_table_name}' not found. Creating...")
            self.create_doc_table(table_name)
            self.documentation["structured"][table_name] = {}
            return

        try:
            response.raise_for_status()
            doc_rows = response.json()
            doc_data = {row['column_name']: row['description'] for row in doc_rows}
            self.documentation["structured"][table_name] = doc_data
        except requests.exceptions.HTTPError as e:
            print(f"❌ Failed to fetch or create documentation table: {e}")
            self.documentation["structured"][table_name] = {}

    def create_doc_table(self, table_name: str):
        doc_table_name = f"_{table_name}"
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.schema}."{doc_table_name}" (
            column_name TEXT,
            description TEXT
        );
        """
        url = f"{self.supabase_url}/rest/v1/rpc/execute_sql"
        response = requests.post(url, headers=self.headers, json={"query": sql})
        response.raise_for_status()
        print(f"✅ Created doc table {doc_table_name}")


    def update_table_doc(self, table_name: str, column_docs: Dict[str, str]):
        doc_table_name = f"_{table_name}"
        for column, description in column_docs.items():
            url = f"{self.supabase_url}/rest/v1/{doc_table_name}"
            payload = {"column_name": column, "description": description}
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

        self.documentation["structured"][table_name] = column_docs
        print(f"✅ Updated documentation for '{table_name}'")

    def fetch_unstructured_collections(self, whitelist: Optional[List[str]] = None):
        collections = self.qdrant_client.get_collections().collections
        collection_names = [col.name for col in collections]

        if whitelist:
            collection_names = [col for col in collection_names if col in whitelist]

        return collection_names

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
