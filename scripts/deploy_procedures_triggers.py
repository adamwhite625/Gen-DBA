import oracledb
import sys
from dotenv import load_dotenv

load_dotenv()
from app.config import settings

def deploy_sp_and_triggers():
    print("Connecting to Oracle PDB (Site 1)...")
    try:
        conn = oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=settings.ORACLE_DSN
        )
        cur = conn.cursor()
        
        # We need to drop constraints/triggers/procedures if they exist to avoid errors
        objects_to_drop = [
            "ALTER TABLE orders_main DROP CONSTRAINT fk_orders_customer",
            "DROP PROCEDURE sp_get_orders_by_date",
            "DROP PROCEDURE sp_revenue_by_month",
            "DROP FUNCTION fn_customer_revenue"
        ]
        for cmd in objects_to_drop:
            try:
                cur.execute(cmd)
            except:
                pass

        print("1. Creating Stored Procedure: sp_get_orders_by_date...")
        cur.execute("""
            CREATE OR REPLACE PROCEDURE sp_get_orders_by_date(
                p_start_date IN DATE,
                p_end_date   IN DATE,
                p_cursor     OUT SYS_REFCURSOR
            ) AS
            BEGIN
                OPEN p_cursor FOR
                    SELECT o_orderkey, o_custkey, o_orderdate, o_totalprice,
                           o_orderpriority, o_clerk
                    FROM orders_full
                    WHERE o_orderdate BETWEEN p_start_date AND p_end_date
                    ORDER BY o_orderdate;
            END;
        """)

        print("2. Creating Stored Procedure: sp_revenue_by_month...")
        cur.execute("""
            CREATE OR REPLACE PROCEDURE sp_revenue_by_month(
                p_year   IN NUMBER,
                p_cursor OUT SYS_REFCURSOR
            ) AS
            BEGIN
                OPEN p_cursor FOR
                    SELECT EXTRACT(MONTH FROM o_orderdate) AS order_month,
                           COUNT(*) AS total_orders,
                           SUM(o_totalprice) AS total_revenue
                    FROM orders_main
                    WHERE EXTRACT(YEAR FROM o_orderdate) = p_year
                    GROUP BY EXTRACT(MONTH FROM o_orderdate)
                    ORDER BY order_month;
            END;
        """)

        print("3. Creating Function: fn_customer_revenue...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION fn_customer_revenue(
                p_custkey IN NUMBER
            ) RETURN NUMBER AS
                v_total NUMBER;
            BEGIN
                SELECT NVL(SUM(o_totalprice), 0) INTO v_total
                FROM orders_main
                WHERE o_custkey = p_custkey;
                RETURN v_total;
            END;
        """)

        print("4. Adding Foreign Key Constraint to orders_main...")
        cur.execute("""
            ALTER TABLE orders_main ADD CONSTRAINT fk_orders_customer
            FOREIGN KEY (o_custkey) REFERENCES customer(c_custkey)
        """)

        print("5. Creating Triggers for distributed synchronization...")
        cur.execute("""
            CREATE OR REPLACE TRIGGER trg_orders_insert
            AFTER INSERT ON orders_main
            FOR EACH ROW
            BEGIN
                INSERT INTO orders_detail@site2_link
                    (o_orderkey, o_orderpriority, o_clerk, o_shippriority, o_comment)
                VALUES
                    (:NEW.o_orderkey, '3-MEDIUM', 'Clerk#000000001', 0, 'auto-generated');
            END;
        """)

        cur.execute("""
            CREATE OR REPLACE TRIGGER trg_orders_delete
            BEFORE DELETE ON orders_main
            FOR EACH ROW
            BEGIN
                DELETE FROM orders_detail@site2_link
                WHERE o_orderkey = :OLD.o_orderkey;
            END;
        """)

        conn.commit()
        print("\nSuccessfully deployed all Stored Procedures, Functions, Constraints, and Triggers!")

    except Exception as e:
        print(f"Deployment Error: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    deploy_sp_and_triggers()
