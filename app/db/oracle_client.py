import oracledb
from app.config import settings

class OracleClient:
    """Client to execute SQL and DDL commands on Oracle 19c."""
    
    def __init__(self):
        self.params = {
            "user": settings.ORACLE_USER,
            "password": settings.ORACLE_PASSWORD,
            "dsn": settings.ORACLE_DSN
        }
        if hasattr(oracledb, "init_oracle_client"):
            oracledb.init_oracle_client()
        oracledb.defaults.fetch_lobs = False

    def get_connection(self):
        """Create and return a new database connection."""
        return oracledb.connect(**self.params)

    def execute_query(self, sql: str, params: dict = None):
        """Execute a SELECT query and return results as a list of dictionaries."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, params or {})
            columns = [col[0] for col in cur.description]
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()

    def execute_ddl(self, ddl: str):
        """Execute a DDL statement."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(ddl)
            conn.commit()
            return {"success": True, "message": "DDL executed successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            conn.close()

    def test_connection(self):
        """Test the connection to Oracle."""
        try:
            conn = self.get_connection()
            version = conn.version
            conn.close()
            return {"connected": True, "version": version}
        except Exception as e:
            return {"connected": False, "error": str(e)}

oracle_client = OracleClient()
