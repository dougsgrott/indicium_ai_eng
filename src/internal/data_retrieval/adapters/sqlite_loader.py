import os
import sqlite3
import pandas as pd
from ..ports.clinical_data import ClinicalDataPort

class SqliteSragAdapter(ClinicalDataPort):
    def __init__(self, db_uri: str, root_dir: str = None):
        """
        Args:
            db_uri: The database URI (e.g., 'sqlite:///data/db.sqlite')
            root_dir: Optional root directory to resolve relative paths against.
        """
        self.db_path = self._resolve_path(db_uri, root_dir)

    def _resolve_path(self, uri: str, root_dir: str) -> str:
        # Strip protocol
        path = uri.replace("sqlite:///", "")
        
        # Resolve relative paths if a root is provided
        if root_dir and not os.path.isabs(path):
            path = os.path.join(root_dir, path)
            
        if not os.path.exists(path):
            raise FileNotFoundError(f"Database file not found at: {path}")
            
        return path

    def get_raw_srag_data(self) -> pd.DataFrame:
        print(f"Adapter connecting to SQLite DB at {self.db_path}...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 1. Dynamic Table Detection
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                if not tables:
                    raise ValueError("The database is empty (no tables found).")
                
                # Default to first, or prioritize known table names
                table_name = tables[0][0]
                for t in tables:
                    name = t[0].lower()
                    if "srag" in name or "influd" in name:
                        table_name = t[0]
                        break
                
                print(f"Adapter detected table: '{table_name}'")

                # 2. Optimized Query
                query = f"SELECT DT_NOTIFIC, EVOLUCAO, UTI, VACINA FROM {table_name}"
                df = pd.read_sql_query(query, conn)
                
                # 3. Basic Cleaning (Schema Compliance)
                df['UTI'] = df['UTI'].fillna(9) 
                
                print(f"Adapter loaded {len(df)} rows.")
                return df

        except Exception as e:
            print(f"Adapter Error: {e}")
            raise e