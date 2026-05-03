import oracledb
import sys
import time

def setup_pdb2():
    print("Connecting to CDB (orcl2) as SYSDBA...")
    try:
        conn = oracledb.connect(
            user='sys',
            password='Thien123456',
            dsn='localhost:1521/orcl2',
            mode=oracledb.SYSDBA
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if PDB2 already exists
        cur.execute("SELECT name FROM v$pdbs WHERE name = 'ORCLPDB2'")
        if cur.fetchone():
            print("PDB ORCLPDB2 already exists.")
        else:
            print("Creating PDB ORCLPDB2 from seed...")
            # FILE_NAME_CONVERT path needs to be correct for the specific Oracle installation.
            # However, Oracle 19c often uses OMF (Oracle Managed Files).
            # We can try without FILE_NAME_CONVERT first.
            try:
                cur.execute("CREATE PLUGGABLE DATABASE orclpdb2 ADMIN USER pdb2admin IDENTIFIED BY pdb2admin123")
                print("Successfully created PDB orclpdb2.")
            except oracledb.DatabaseError as e:
                print(f"Failed to create PDB without FILE_NAME_CONVERT: {e}")
                # Try with FILE_NAME_CONVERT
                print("Trying with FILE_NAME_CONVERT...")
                cur.execute("CREATE PLUGGABLE DATABASE orclpdb2 ADMIN USER pdb2admin IDENTIFIED BY pdb2admin123 FILE_NAME_CONVERT = ('pdbseed', 'orclpdb2')")
                print("Successfully created PDB orclpdb2 with FILE_NAME_CONVERT.")

        # Open PDB2
        try:
            cur.execute("ALTER PLUGGABLE DATABASE orclpdb2 OPEN")
            print("PDB ORCLPDB2 opened.")
        except Exception as e:
            print(f"PDB might already be open: {e}")

        try:
            cur.execute("ALTER PLUGGABLE DATABASE orclpdb2 SAVE STATE")
        except:
            pass

        cur.close()
        conn.close()
        
        # Now connect directly to PDB2
        print("\nConnecting to PDB2 (orclpdb2) as SYSDBA...")
        time.sleep(2) # Give it a moment to register with listener
        conn2 = oracledb.connect(
            user='sys',
            password='Thien123456',
            dsn='localhost:1521/orclpdb2',
            mode=oracledb.SYSDBA
        )
        cur2 = conn2.cursor()
        
        commands = [
            "CREATE USER gendba IDENTIFIED BY gendba123",
            "GRANT CONNECT, RESOURCE, DBA TO gendba",
            "GRANT SELECT ANY DICTIONARY TO gendba",
            "GRANT CREATE DATABASE LINK TO gendba"
        ]
        
        print("Setting up user 'gendba' on Site 2...")
        for cmd in commands:
            try:
                cur2.execute(cmd)
                print(f"  Success: {cmd}")
            except oracledb.DatabaseError as e:
                error_obj, = e.args
                if error_obj.code == 1920: # ORA-01920: user name conflicts with another user
                    print(f"  User already exists: {cmd}")
                else:
                    print(f"  Error executing '{cmd}': {e}")
        
        conn2.commit()
        cur2.close()
        conn2.close()
        print("\nSite 2 (orclpdb2) setup completed successfully!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_pdb2()
