import json
import requests
import os
from typing import Dict, Any, List

# Load credentials from config.json
key_path = os.path.join(os.path.dirname(__file__), '..', 'keys.json')
with open(key_path, 'r') as f:
    config = json.load(f)
pg_config = config["postgres"]

class StructuredDB:
    def __init__(self, table_name: str = None, schema: str = "public"):
        self.supabase_url = pg_config["SUPABASE_URL"]
        self.api_key = pg_config["SUPABASE_API_KEY"]
        self.table_name = table_name or pg_config["SUPABASE_TABLE"]
        self.schema = schema or pg_config["SUPABASE_SCHEMA"]

        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def create_table(self, sql_create_query: str) -> Dict:
        """
        Create a table by executing raw SQL via a stored procedure
        Assumes you have a stored function `execute_sql(query text)`
        """
        url = f"{self.supabase_url}/rest/v1/rpc/execute_sql"
        payload = {"query": sql_create_query}

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json() if response.content else {"status": "success"}
    
    def read_rows(self, select: str = "*", filters: Dict[str, Any] = None) -> List[Dict]:
        """
        Read rows from the table with optional filters
        Args:
            select: Columns to select (default: "*")
            filters: Dictionary of column filters (e.g., {"column": "value"})
        """
        url = f"{self.supabase_url}/rest/v1/{self.table_name}?select={select}"
        
        if filters:
            filter_str = "&".join([f"{k}=eq.{v}" for k, v in filters.items()])
            url += f"&{filter_str}"
            
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_row(self, row_id: int, update_data: Dict[str, Any]) -> Dict:
        """
        Update a row by ID
        Args:
            row_id: The ID of the row to update
            update_data: Dictionary of column-value pairs to update
        """
        url = f"{self.supabase_url}/rest/v1/{self.table_name}?id=eq.{row_id}"
        response = requests.patch(url, headers=self.headers, json=update_data)
        response.raise_for_status()
        return response.json()

    def insert_row(self, data: Dict[str, Any]) -> Dict:
        """
        Insert a new row
        Args:
            data: Dictionary of column-value pairs to insert
        """
        url = f"{self.supabase_url}/rest/v1/{self.table_name}"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def delete_row(self, row_id: int) -> None:
        """
        Delete a row by ID
        Args:
            row_id: The ID of the row to delete
        """
        url = f"{self.supabase_url}/rest/v1/{self.table_name}?id=eq.{row_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
