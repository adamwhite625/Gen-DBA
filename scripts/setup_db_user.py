import oracledb
import sys

def create_gendba_user():
    try:
        conn = oracledb.connect(
            user='sys',
            password='Thien123456',
            dsn='localhost:1521/orcl2',
            mode=oracledb.SYSDBA
        )
        cur = conn.cursor()
        
        commands = [
            "CREATE USER gendba IDENTIFIED BY gendba123",
            "GRANT CONNECT, RESOURCE, DBA TO gendba",
            "GRANT SELECT ANY DICTIONARY TO gendba",
            "GRANT SELECT ON v_$sql TO gendba",
            "GRANT SELECT ON v_$sqlarea TO gendba",
            "GRANT SELECT ON v_$sql_plan TO gendba",
            "GRANT SELECT ON dba_tab_partitions TO gendba",
            "GRANT SELECT ON dba_tab_statistics TO gendba",
            "GRANT ALTER ANY TABLE TO gendba",
            "GRANT CREATE ANY TABLE TO gendba",
            "GRANT DROP ANY TABLE TO gendba",
            "GRANT EXECUTE ON dbms_xplan TO gendba"
        ]
        
        for cmd in commands:
            try:
                cur.execute(cmd)
                print(f"Success: {cmd}")
            except oracledb.DatabaseError as e:
                error_obj, = e.args
                if error_obj.code == 1920: # ORA-01920: user name conflicts with another user
                    print(f"User already exists: {cmd}")
                else:
                    print(f"Error executing '{cmd}': {e}")
        
        conn.commit()
        print("\nSetup of user 'gendba' completed in orclpdb!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_gendba_user()
