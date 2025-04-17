import sqlite3
import os
from typing import Dict, Any, List, Optional


class StructuredDB:
    def __init__(self, db_path: str, table_name: Optional[str] = None):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # allows dictionary-like rows
        self.cursor = self.conn.cursor()
        self.table_name = table_name

    def create_table(self, sql_create_query: str) -> Dict[str, str]:
        """
        Execute a SQL query to create a table
        """
        self.cursor.execute(sql_create_query)
        self.conn.commit()
        return {"status": "success"}

    def read_rows(self, select: str = "*", filters: Dict[str, Any] = None) -> List[Dict]:
        """
        Read rows from the table with optional filters
        """
        query = f"SELECT {select} FROM {self.table_name}"
        values = []

        if filters:
            conditions = [f"{col} = ?" for col in filters]
            query += " WHERE " + " AND ".join(conditions)
            values = list(filters.values())

        self.cursor.execute(query, values)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def insert_row(self, data: Dict[str, Any]) -> Dict:
        """
        Insert a new row into the table
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(query, list(data.values()))
        self.conn.commit()
        return {"status": "inserted", "rowid": self.cursor.lastrowid}

    def update_row(self, row_id: int, update_data: Dict[str, Any], id_column: str = "id") -> Dict:
        """
        Update a row by ID
        """
        set_clause = ", ".join([f"{col} = ?" for col in update_data])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {id_column} = ?"
        values = list(update_data.values()) + [row_id]
        self.cursor.execute(query, values)
        self.conn.commit()
        return {"status": "updated", "rowcount": self.cursor.rowcount}

    def delete_row(self, row_id: int, id_column: str = "id") -> Dict:
        """
        Delete a row by ID
        """
        query = f"DELETE FROM {self.table_name} WHERE {id_column} = ?"
        self.cursor.execute(query, (row_id,))
        self.conn.commit()
        return {"status": "deleted", "rowcount": self.cursor.rowcount}

    def close(self):
        self.conn.close()
