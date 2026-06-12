import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime


class ShopAnalytics:
    def __init__(self, db_name="shop_data.db"):
        self.db_name = db_name
        self.conn = None
        self.df_orders = None
        self.df_users = None

        sns.set(style="whitegrid")
        plt.rcParams["figure.figsize"] = (12, 6)

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)

    def close(self):
        if self.conn:
            self.conn.close()

    def load_data(self):
        """
        بارگذاری داده‌ها از دیتابیس
        """
        self.df_orders = pd.read_sql_query("SELECT * FROM orders", self.conn)
        self.df_users = pd.read_sql_query("SELECT * FROM users", self.conn)

        # تبدیل نوع داده‌ها
        if "order_date" in self.df_orders.columns:
            self.df_orders["order_date"] = pd.to_datetime(self.df_orders["order_date"], errors="coerce")

        if "quantity" in self.df_orders.columns:
            self.df_orders["quantity"] = pd.to_numeric(self.df_orders["quantity"], errors="coerce")

        if "price" in self.df_orders.columns:
            self.df_orders["price"] = pd.to_numeric(self.df_orders["price"], errors="coerce")

        if "date_signup" in self.df_users.columns:
            self.df_users["date_signup"] = pd.to_datetime(self.df_users["date_signup"], errors="coerce")

        # ساخت revenue
        self.df_orders["revenue"] = self.df_orders["quantity"] * self.df_orders["price"]

    def run_query(self, query):
        return pd.read_sql_query(query, self.conn)

    #---------------------------------------------------------
    def analysis_1_category_sales(self):
        query = """
            SELECT 
                category,
                SUM(quantity * price) AS total_sales
            FROM orders
            GROUP BY category
            ORDER BY total_sales DESC
        """
        df = self.run_query(query)

        plt.figure()
        sns.barplot(data=df, x="category", y="total_sales", palette="Blues_r")
        plt.title("1) فروش به تفکیک دسته‌بندی محصولات")
        plt.xlabel("دسته‌بندی")
        plt.ylabel("فروش کل")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()

        return df

    # ---------------------------------------------------------
    # 2) 
    # ---------------------------------------------------------
    def analysis_2_monthly_sales(self):
        query = """
            SELECT 
                strftime('%Y-%m', order_date) AS month,
                SUM(quantity * price) AS total_sales
            FROM orders
            GROUP BY month
            ORDER BY month
        """
        df = self.run_query(query)

        plt.figure()
        sns.lineplot(data=df, x="month", y="total_sales", marker="o")
        plt.title("2) روند فروش ماهانه")
        plt.xlabel("ماه")
        plt.ylabel("فروش کل")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

        return df

    # ---------------------------------------------------------
    # 3) 
    # ---------------------------------------------------------
    def analysis_3_top_products(self, top_n=5):
        query = f"""
            SELECT 
                product,
                SUM(quantity * price) AS total_sales
            FROM orders
            GROUP BY product
            ORDER BY total_sales DESC
            LIMIT {top_n}
        """
        df = self.run_query(query)

        plt.figure()
        sns.barplot(data=df, y="product", x="total_sales", palette="Greens_r")
        plt.title(f"3) {top_n} محصول پرفروش")
        plt.xlabel("فروش کل")
        plt.ylabel("محصول")
        plt.tight_layout()
        plt.show()

        return df

    # ---------------------------------------------------------
    # 4) 
    # ---------------------------------------------------------
    def analysis_4_city_sales_valid(self, valid_cities=None):
        if valid_cities is None:
            valid_cities = ["Tehran", "Mashhad", "Shiraz", "Isfahan", "Tabriz"]

        placeholders = ",".join(["?"] * len(valid_cities))
        query = f"""
            SELECT 
                city,
                SUM(quantity * price) AS total_sales
            FROM orders
            WHERE city IN ({placeholders})
            GROUP BY city
            ORDER BY total_sales DESC
        """
        df = pd.read_sql_query(query, self.conn, params=valid_cities)

        plt.figure()
        plt.pie(df["total_sales"], labels=df["city"], autopct="%1.1f%%", startangle=140)
        plt.title("4) فروش به تفکیک شهر‌های معتبر")
        plt.tight_layout()
        plt.show()

        return df

    # ---------------------------------------------------------
    # 5) 
    # ---------------------------------------------------------
    def analysis_5_price_distribution(self):
        query = """
            SELECT price
            FROM orders
            WHERE price IS NOT NULL
        """
        df = self.run_query(query)

        plt.figure()
        sns.histplot(df["price"], bins=20, kde=True, color="purple")
        plt.title("5) توزیع قیمت محصولات")
        plt.xlabel("قیمت")
        plt.ylabel("تعداد")
        plt.tight_layout()
        plt.show()

        return df

    # ---------------------------------------------------------
    # 6) 
    # ---------------------------------------------------------
    def analysis_6_orders_per_customer(self):
        query = """
            SELECT 
                customer_id,
                COUNT(*) AS order_count
            FROM orders
            GROUP BY customer_id
            ORDER BY order_count DESC
        """
        df = self.run_query(query)

        plt.figure()
        sns.barplot(data=df.head(20), x="customer_id", y="order_count", palette="Oranges_r")
        plt.title("6) تعداد سفارشات هر مشتری")
        plt.xlabel("شناسه مشتری")
        plt.ylabel("تعداد سفارش")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

        return df

    # ---------------------------------------------------------
    # 7)
    # ---------------------------------------------------------
    def analysis_7_signup_behavior(self, pivot_date="2024-01-01"):
        query = """
            SELECT 
                u.user_id,
                u.signup_date,
                CASE 
                    WHEN date(u.signup_date) < date(?) THEN 'قبل از تاریخ مبنا'
                    ELSE 'بعد از تاریخ مبنا'
                END AS signup_group,
                COUNT(o.order_id) AS order_count
            FROM users u
            LEFT JOIN orders o
                ON u.user_id = o.customer_id
            GROUP BY u.user_id, u.signup_date, signup_group
            ORDER BY signup_group
        """
        df = pd.read_sql_query(query, self.conn, params=[pivot_date])

        grouped = df.groupby("signup_group", as_index=False)["order_count"].sum()

        plt.figure()
        sns.barplot(data=grouped, x="signup_group", y="order_count", palette="Set2")
        plt.title("7) رفتار خرید مشتریان بر اساس تاریخ ثبت‌نام")
        plt.xlabel("گروه ثبت‌نام")
        plt.ylabel("تعداد سفارش")
        plt.tight_layout()
        plt.show()

        return df

    # ---------------------------------------------------------
    # اجرای همه تحلیل‌ها
    # ---------------------------------------------------------
    def run_all(self):
        self.connect()
        self.load_data()

        print("\n--- تحلیل 1 ---")
        print(self.analysis_1_category_sales())

        print("\n--- تحلیل 2 ---")
        print(self.analysis_2_monthly_sales())

        print("\n--- تحلیل 3 ---")
        print(self.analysis_3_top_products())

        print("\n--- تحلیل 4 ---")
        print(self.analysis_4_city_sales_valid())

        print("\n--- تحلیل 5 ---")
        print(self.analysis_5_price_distribution())

        print("\n--- تحلیل 6 ---")
        print(self.analysis_6_orders_per_customer())

        print("\n--- تحلیل 7 ---")
        print(self.analysis_7_signup_behavior())

        self.close()


if __name__ == "__main__":
    analytics = ShopAnalytics("shop_data.db")
    analytics.run_all()
