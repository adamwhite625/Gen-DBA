"""Trinh quan ly ket noi Oracle su dung python-oracledb."""
import oracledb
from app.config import settings

class OracleClient:
    """Client de thuc thi SQL va DDL tren Oracle 19c."""
    
    def __init__(self):
        self.params = {
            "user": settings.ORACLE_USER,
            "password": settings.ORACLE_PASSWORD,
            "dsn": settings.ORACLE_DSN
        }
        # Khoi tao thin mode mac dinh
        oracledb.init_oracle_client() if hasattr(oracledb, "init_oracle_client") else None

    def get_connection(self):
        """Tao va tra ve ket noi moi."""
        return oracledb.connect(**self.params)

    def execute_query(self, sql: str, params: dict = None):
        """Thuc thi truy van SELECT va tra ve danh sach dictionary."""
        conn = self.get_connection()
        try:
            conn.rowfactory = lambda *args: dict(zip([d[0] for d in cur.description], args))
            cur = conn.cursor()
            cur.execute(sql, params or {})
            return cur.fetchall()
        finally:
            conn.close()

    def execute_ddl(self, ddl: str):
        """Thuc thi lenh DDL (ALTER, CREATE, v.v.)."""
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
        """Kiem tra ket noi den Oracle."""
        try:
            conn = self.get_connection()
            version = conn.version
            conn.close()
            return {"connected": True, "version": version}
        except Exception as e:
            return {"connected": False, "error": str(e)}

oracle_client = OracleClient()
