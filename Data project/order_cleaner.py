import pandas as pd
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_processing.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


class OrderCleaner:
    def __init__(self, input_csv: str, output_csv: str = "cleaned_orders.csv"):
        self.input_csv = input_csv
        self.output_csv = output_csv
        self.required_columns = [
            'order_id', 'customer_id', 'city', 'product', 'category',
            'quantity', 'price', 'order_date'
        ]
        self.numeric_columns = ['order_id', 'customer_id', 'quantity', 'price']
        logging.info("OrderCleaner initialized.")

    def load_data(self) -> pd.DataFrame:
        """Load orders data from CSV."""
        try:
            df = pd.read_csv(self.input_csv)
            logging.info(f"Loaded orders file: {self.input_csv} with {len(df)} rows.")
            return df
        except Exception as e:
            logging.error(f"Error reading orders file: {e}")
            raise

    def remove_duplicates(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        """Remove duplicate orders based on order_id."""
        initial_count = len(df)
        duplicate_mask = df.duplicated(subset=['order_id'], keep='first')
        duplicate_count = int(duplicate_mask.sum())
        df = df.loc[~duplicate_mask].copy()

        logging.info(f"Duplicate orders found and removed: {duplicate_count}")
        logging.info(f"Rows before duplicate removal: {initial_count}")
        logging.info(f"Rows after duplicate removal: {len(df)}")
        return df, duplicate_count

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean orders data."""
        # Keep only required columns if extra columns exist
        missing_required = [col for col in self.required_columns if col not in df.columns]
        if missing_required:
            raise ValueError(f"Missing required columns in orders CSV: {missing_required}")

        df = df[self.required_columns].copy()

        # Drop rows with missing required values
        df = df.dropna(subset=self.required_columns)

        # Convert numeric columns safely
        for col in self.numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.dropna(subset=self.numeric_columns)

        # Remove invalid numeric values
        df = df[(df['quantity'] > 0) & (df['price'] >= 0)]

        # Clean text columns
        for col in ['product', 'category']:
            df[col] = df[col].astype(str).str.strip()

        # Parse and format dates
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        df = df.dropna(subset=['order_date'])
        df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')

        # Convert integer-like columns back to int
        df['order_id'] = df['order_id'].astype(int)
        df['customer_id'] = df['customer_id'].astype(int)
        df['quantity'] = df['quantity'].astype(int)
        df['price'] = df['price'].astype(float)

        return df

    def save_cleaned_data(self, df: pd.DataFrame) -> None:
        """Save cleaned orders to CSV."""
        try:
            df.to_csv(self.output_csv, index=False, encoding="utf-8-sig")
            logging.info(f"Cleaned orders saved to: {self.output_csv}")
        except Exception as e:
            logging.error(f"Error saving cleaned orders: {e}")
            raise

    def process(self) -> pd.DataFrame:
        """Run full cleaning pipeline."""
        df = self.load_data()
        df, _ = self.remove_duplicates(df)
        cleaned_df = self.clean_data(df)
        self.save_cleaned_data(cleaned_df)

        logging.info(f"Final cleaned orders count: {len(cleaned_df)}")
        return cleaned_df


if __name__ == "__main__":
    cleaner = OrderCleaner("orders.csv")
    cleaned_orders = cleaner.process()
    print(cleaned_orders.head(10))

