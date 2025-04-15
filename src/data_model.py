import os
import json
import requests
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class DataModel:
    def __init__(self, structured_cfg, vector_cfg, schema="public"):
        # Load structured DB config
        self.supabase_url = structured_cfg["SUPABASE_URL"]
        self.api_key = structured_cfg["SUPABASE_API_KEY"]
        self.schema = schema
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Load vector DB config
        self.qdrant_client = QdrantClient(url=vector_cfg["url"], api_key=vector_cfg["api_key"])
        self.vector_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Internal documentation
        self.documentation = {"structured": {}, "unstructured": {}}

    def fetch_tables(self, whitelist: Optional[List[str]] = None):
        url = f"{self.supabase_url}/rest/v1/?select=table_name&schema={self.schema}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        tables = [tbl["table_name"] for tbl in response.json()]

        if whitelist:
            tables = [table for table in tables if table in whitelist]

        return tables

    def fetch_or_init_table_doc(self, table_name):
        doc_table_name = f"_{table_name}"
        url = f"{self.supabase_url}/rest/v1/{doc_table_name}?select=*"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 404:
            # Create documentation table with empty descriptions
            self.create_doc_table(table_name)
            doc_data = {}
        else:
            response.raise_for_status()
            doc_rows = response.json()
            doc_data = {row['column_name']: row['description'] for row in doc_rows}

        self.documentation["structured"][table_name] = doc_data

    def create_doc_table(self, table_name):
        doc_table_name = f"_{table_name}"
        create_table_sql = {
            "name": doc_table_name,
            "schema": self.schema,
            "columns": [
                {"name": "column_name", "type": "text"},
                {"name": "description", "type": "text"}
            ]
        }
        url = f"{self.supabase_url}/rest/v1/rpc/create_table"
        response = requests.post(url, headers=self.headers, json=create_table_sql)
        response.raise_for_status()

    def update_table_doc(self, table_name, column_docs: Dict[str, str]):
        doc_table_name = f"_{table_name}"
        for column, description in column_docs.items():
            url = f"{self.supabase_url}/rest/v1/{doc_table_name}"
            payload = {"column_name": column, "description": description}
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

        self.documentation["structured"][table_name] = column_docs

    def fetch_unstructured_collections(self, whitelist: Optional[List[str]] = None):
        collections = self.qdrant_client.get_collections().collections
        collection_names = [col.name for col in collections]

        if whitelist:
            collection_names = [col for col in collection_names if col in whitelist]

        return collection_names

    def add_unstructured_doc(self, collection_name, description, update_db: bool = False):
        if update_db:
            self.qdrant_client.set_collection_alias(collection_name, description)
        self.documentation["unstructured"][collection_name] = description

    def get_documentation_dict(self):
        return self.documentation
