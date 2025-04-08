import sqlite3
from typing import List, Tuple

class StructuredDB:
    def __init__(self, db_path: str = 'local.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def create_table(self, table_name: str, columns: str):
        create_stmt = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});"
        self.cursor.execute(create_stmt)
        self.conn.commit()

    def insert_record(self, table_name: str, columns: List[str], values: List[Tuple]):
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        insert_stmt = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders});"
        self.cursor.executemany(insert_stmt, values)
        self.conn.commit()

    def fetch_all(self, table_name: str) -> List[Tuple]:
        select_stmt = f"SELECT * FROM {table_name};"
        self.cursor.execute(select_stmt)
        return self.cursor.fetchall()

    def delete_all(self, table_name: str):
        delete_stmt = f"DELETE FROM {table_name};"
        self.cursor.execute(delete_stmt)
        self.conn.commit()

    def close(self):
        self.conn.close()
