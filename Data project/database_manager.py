import pandas as pd
import sqlite3
import logging


class ShopDatabase:
    def __init__(self, db_name="shop_data.db"):
        self.db_name = db_name
        self.orders_table = "orders"
        self.users_table = "users"
        logging.info("راه‌اندازی دیتابیس انجام شد.")

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_tables(self):
        """Create tables for orders and users."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.orders_table} (
                    order_id INTEGER,
                    customer_id INTEGER,
                    city TEXT,
                    product TEXT,
                    category TEXT,
                    quantity INTEGER,
                    price REAL,
                    order_date TEXT
                )
            """)

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.users_table} (
                    id_user INTEGER,
                    name_full TEXT,
                    email TEXT,
                    date_signup TEXT,
                    city TEXT
                )
            """)

            conn.commit()
            logging.info("جدول‌های orders و users ساخته شدند.")

    def load_csv(self, csv_path: str) -> pd.DataFrame:
        """Load a CSV file into a DataFrame."""
        logging.info(f"خواندن فایل: {csv_path}")
        return pd.read_csv(csv_path)

    def save_dataframe(self, df: pd.DataFrame, table_name: str):
        """Save a DataFrame into SQLite."""
        with self._get_connection() as conn:
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            conn.commit()
            logging.info(f"{len(df)} رکورد در جدول {table_name} ذخیره شد.")

    def import_orders_from_clean_csv(self, csv_path: str):
        """
        Read cleaned orders CSV and save it into orders table.
        """
        df = self.load_csv(csv_path)
        self.save_dataframe(df, self.orders_table)

    def import_users_as_is(self, csv_path: str):
        """
        Read users CSV and save it as-is into users table.
        """
        df = self.load_csv(csv_path)
        self.save_dataframe(df, self.users_table)

    def run_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query on SQLite database."""
        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("data_processing.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    db = ShopDatabase()
    db.create_tables()

    # Load data
    db.import_orders_from_clean_csv("cleaned_orders.csv")
    db.import_users_as_is("users.csv")

    print("داده‌ها با موفقیت در SQLite ذخیره شدند.")

    print("\nOrders sample:")
    print(db.run_query("SELECT * FROM orders LIMIT 5"))

    print("\nUsers sample:")
    print(db.run_query("SELECT * FROM users LIMIT 5"))

    print("\nJoin sample:")
    print(db.run_query("""
        SELECT 
            o.order_id,
            o.customer_id,
            u.user_id,
            u.full_name,
            u.email,
            u.signup_date,
            u.city AS user_city,
            o.product,
            o.category,
            o.quantity,
            o.price,
            o.order_date,
            o.city AS order_city
        FROM orders o
        INNER JOIN users u
            ON o.customer_id = user_id
        LIMIT 5
    """))
