"""Sinh dữ liệu TPC-H cho Oracle để phục vụ kiểm thử Gen-DBA."""
import random
import datetime
import oracledb
import sys

# Cấu hình kết nối (Sử dụng PDB orclpdb)
DB_USER = "gendba"
DB_PASSWORD = "gendba123"
DB_DSN = "localhost:1521/orclpdb"

# Scale factor quy định kích thước dữ liệu (0.1 = ~100MB, 1 = ~1GB)
SCALE_FACTOR = 0.1

def create_tables(cursor):
    """Tạo các bảng theo schema TPC-H."""
    ddl_statements = [
        """
        CREATE TABLE region (
            r_regionkey NUMBER NOT NULL,
            r_name CHAR(25) NOT NULL,
            r_comment VARCHAR2(152),
            CONSTRAINT region_pk PRIMARY KEY (r_regionkey)
        )
        """,
        """
        CREATE TABLE nation (
            n_nationkey NUMBER NOT NULL,
            n_name CHAR(25) NOT NULL,
            n_regionkey NUMBER NOT NULL,
            n_comment VARCHAR2(152),
            CONSTRAINT nation_pk PRIMARY KEY (n_nationkey)
        )
        """,
        """
        CREATE TABLE customer (
            c_custkey NUMBER NOT NULL,
            c_name VARCHAR2(25) NOT NULL,
            c_address VARCHAR2(40) NOT NULL,
            c_nationkey NUMBER NOT NULL,
            c_phone CHAR(15) NOT NULL,
            c_acctbal NUMBER(12,2) NOT NULL,
            c_mktsegment CHAR(10) NOT NULL,
            c_comment VARCHAR2(117),
            CONSTRAINT customer_pk PRIMARY KEY (c_custkey)
        )
        """,
        """
        CREATE TABLE orders (
            o_orderkey NUMBER NOT NULL,
            o_custkey NUMBER NOT NULL,
            o_orderstatus CHAR(1) NOT NULL,
            o_totalprice NUMBER(12,2) NOT NULL,
            o_orderdate DATE NOT NULL,
            o_orderpriority CHAR(15) NOT NULL,
            o_clerk CHAR(15) NOT NULL,
            o_shippriority NUMBER NOT NULL,
            o_comment VARCHAR2(79),
            CONSTRAINT orders_pk PRIMARY KEY (o_orderkey)
        )
        """,
        """
        CREATE TABLE lineitem (
            l_orderkey NUMBER NOT NULL,
            l_partkey NUMBER NOT NULL,
            l_suppkey NUMBER NOT NULL,
            l_linenumber NUMBER NOT NULL,
            l_quantity NUMBER(12,2) NOT NULL,
            l_extendedprice NUMBER(12,2) NOT NULL,
            l_discount NUMBER(12,2) NOT NULL,
            l_tax NUMBER(12,2) NOT NULL,
            l_returnflag CHAR(1) NOT NULL,
            l_linestatus CHAR(1) NOT NULL,
            l_shipdate DATE NOT NULL,
            l_commitdate DATE NOT NULL,
            l_receiptdate DATE NOT NULL,
            l_shipinstruct CHAR(25) NOT NULL,
            l_shipmode CHAR(10) NOT NULL,
            l_comment VARCHAR2(44),
            CONSTRAINT lineitem_pk PRIMARY KEY (l_orderkey, l_linenumber)
        )
        """,
        """
        CREATE TABLE supplier (
            s_suppkey NUMBER NOT NULL,
            s_name CHAR(25) NOT NULL,
            s_address VARCHAR2(40) NOT NULL,
            s_nationkey NUMBER NOT NULL,
            s_phone CHAR(15) NOT NULL,
            s_acctbal NUMBER(12,2) NOT NULL,
            s_comment VARCHAR2(101),
            CONSTRAINT supplier_pk PRIMARY KEY (s_suppkey)
        )
        """,
        """
        CREATE TABLE part (
            p_partkey NUMBER NOT NULL,
            p_name VARCHAR2(55) NOT NULL,
            p_mfgr CHAR(25) NOT NULL,
            p_brand CHAR(10) NOT NULL,
            p_type VARCHAR2(25) NOT NULL,
            p_size NUMBER NOT NULL,
            p_container CHAR(10) NOT NULL,
            p_retailprice NUMBER(12,2) NOT NULL,
            p_comment VARCHAR2(23),
            CONSTRAINT part_pk PRIMARY KEY (p_partkey)
        )
        """,
        """
        CREATE TABLE partsupp (
            ps_partkey NUMBER NOT NULL,
            ps_suppkey NUMBER NOT NULL,
            ps_availqty NUMBER NOT NULL,
            ps_supplycost NUMBER(12,2) NOT NULL,
            ps_comment VARCHAR2(199),
            CONSTRAINT partsupp_pk PRIMARY KEY (ps_partkey, ps_suppkey)
        )
        """
    ]

    for ddl in ddl_statements:
        table_name = ddl.strip().split("CREATE TABLE ")[1].split(" ")[0].strip(" (")
        try:
            cursor.execute(f"DROP TABLE {table_name} CASCADE CONSTRAINTS")
        except:
            pass
        cursor.execute(ddl)
        print(f"  Created table: {table_name}")


def generate_data(cursor, conn, scale_factor=0.1):
    """Chèn dữ liệu mẫu TPC-H."""
    num_orders = int(150000 * scale_factor)
    num_customers = int(15000 * scale_factor)
    num_suppliers = int(1000 * scale_factor)
    num_parts = int(20000 * scale_factor)

    regions = ['AFRICA', 'AMERICA', 'ASIA', 'EUROPE', 'MIDDLE EAST']
    nations = [
        ('ALGERIA', 0), ('ARGENTINA', 1), ('BRAZIL', 1), ('CANADA', 1),
        ('CHINA', 2), ('EGYPT', 0), ('ETHIOPIA', 0), ('FRANCE', 3),
        ('GERMANY', 3), ('INDIA', 2), ('INDONESIA', 2), ('IRAN', 4),
        ('IRAQ', 4), ('JAPAN', 2), ('JORDAN', 4), ('KENYA', 0),
        ('MOROCCO', 0), ('MOZAMBIQUE', 0), ('PERU', 1), ('ROMANIA', 3),
        ('RUSSIA', 3), ('SAUDI ARABIA', 4), ('UNITED KINGDOM', 3),
        ('UNITED STATES', 1), ('VIETNAM', 2)
    ]
    segments = ['AUTOMOBILE', 'BUILDING', 'FURNITURE', 'HOUSEHOLD', 'MACHINERY']
    priorities = ['1-URGENT', '2-HIGH', '3-MEDIUM', '4-NOT SPECI', '5-LOW']
    shipmodes = ['REG AIR', 'AIR', 'RAIL', 'SHIP', 'TRUCK', 'MAIL', 'FOB']
    ship_instruct = ['DELIVER IN PERSON', 'COLLECT COD', 'NONE', 'TAKE BACK RETURN']

    # Region
    for i, name in enumerate(regions):
        cursor.execute("INSERT INTO region VALUES (:1, :2, :3)", [i, name, f'Region {name} comment'])
    print(f"  Inserted {len(regions)} regions")

    # Nation
    for i, (name, rkey) in enumerate(nations):
        cursor.execute("INSERT INTO nation VALUES (:1, :2, :3, :4)", [i, name, rkey, f'Nation {name}'])
    print(f"  Inserted {len(nations)} nations")

    # Customer
    for i in range(1, num_customers + 1):
        cursor.execute(
            "INSERT INTO customer VALUES (:1,:2,:3,:4,:5,:6,:7,:8)",
            [i, f'Customer#{i:09d}', f'Addr{i}', random.randint(0, 24),
             f'{random.randint(10,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}',
             round(random.uniform(-999.99, 9999.99), 2),
             random.choice(segments), f'comment {i}']
        )
        if i % 1000 == 0:
            conn.commit()
    conn.commit()
    print(f"  Inserted {num_customers} customers")

    # Supplier
    for i in range(1, num_suppliers + 1):
        cursor.execute(
            "INSERT INTO supplier VALUES (:1,:2,:3,:4,:5,:6,:7)",
            [i, f'Supplier#{i:09d}', f'SupAddr{i}', random.randint(0, 24),
             f'{random.randint(10,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}',
             round(random.uniform(-999.99, 9999.99), 2), f'sup comment {i}']
        )
    conn.commit()
    print(f"  Inserted {num_suppliers} suppliers")

    # Part
    for i in range(1, num_parts + 1):
        cursor.execute(
            "INSERT INTO part VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9)",
            [i, f'Part-{i}-name', f'Manufacturer#{random.randint(1,5)}',
             f'Brand#{random.randint(1,5)}{random.randint(1,5)}',
             f'TYPE{random.randint(1,50)}', random.randint(1, 50),
             random.choice(['SM CASE','SM BOX','SM PACK','SM PKG','LG CASE','LG BOX']),
             round(random.uniform(1, 2000), 2), f'part comment {i}']
        )
        if i % 2000 == 0:
            conn.commit()
    conn.commit()
    print(f"  Inserted {num_parts} parts")

    # Orders and Lineitem
    base_date = datetime.date(1992, 1, 1)
    lineitem_count = 0

    for i in range(1, num_orders + 1):
        order_date = base_date + datetime.timedelta(days=random.randint(0, 2556))
        num_items = random.randint(1, 7)
        total = 0

        for j in range(1, num_items + 1):
            qty = random.randint(1, 50)
            price = round(random.uniform(1, 1000), 2)
            discount = round(random.uniform(0, 0.10), 2)
            tax = round(random.uniform(0, 0.08), 2)
            extended = round(qty * price, 2)
            total += extended

            ship_date = order_date + datetime.timedelta(days=random.randint(1, 121))
            commit_date = order_date + datetime.timedelta(days=random.randint(30, 90))
            receipt_date = ship_date + datetime.timedelta(days=random.randint(1, 30))

            cursor.execute(
                "INSERT INTO lineitem VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15,:16)",
                [i, random.randint(1, max(num_parts,1)), random.randint(1, max(num_suppliers,1)),
                 j, qty, extended, discount, tax,
                 random.choice(['R','A','N']), random.choice(['O','F']),
                 ship_date, commit_date, receipt_date,
                 random.choice(ship_instruct), random.choice(shipmodes),
                 f'lineitem comment {i}-{j}']
            )
            lineitem_count += 1

        cursor.execute(
            "INSERT INTO orders VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9)",
            [i, random.randint(1, max(num_customers,1)),
             random.choice(['O','F','P']), round(total, 2),
             order_date, random.choice(priorities),
             f'Clerk#{random.randint(1,1000):09d}',
             0, f'order comment {i}']
        )

        if i % 1000 == 0:
            conn.commit()
            print(f"    Progress: {i}/{num_orders} orders...")

    conn.commit()
    print(f"  Inserted {num_orders} orders and {lineitem_count} lineitems")


if __name__ == "__main__":
    try:
        print(f"Connecting to Oracle ({DB_DSN}) as {DB_USER}...")
        conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        cursor = conn.cursor()

        print("\nCreating TPC-H tables...")
        create_tables(cursor)

        print(f"\nGenerating TPC-H data (Scale Factor = {SCALE_FACTOR})...")
        generate_data(cursor, conn, SCALE_FACTOR)

        print("\nGathering schema statistics...")
        cursor.execute("BEGIN DBMS_STATS.GATHER_SCHEMA_STATS('GENDBA'); END;")

        print("\nVerifying data counts:")
        for table in ['region','nation','customer','orders','lineitem','supplier','part','partsupp']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} rows")

        cursor.close()
        conn.close()
        print("\nTPC-H data generation completed successfully!")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
