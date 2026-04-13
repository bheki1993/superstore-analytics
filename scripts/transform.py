# transform.py
# Purpose: Read raw CSV from S3, clean it, build star schema, load into RDS MySQL

import boto3
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from io import StringIO
import os

# ─── CONFIG ───────────────────────────────────────────────────────────────────
AWS_ACCESS_KEY  = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY  = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION      = "us-east-1"
S3_BUCKET       = "superstore-analytics-bheki"
S3_RAW_KEY      = "raw/superstore.csv"

DB_HOST         = "superstore-db.cwl0g8wsaizq.us-east-1.rds.amazonaws.com"
DB_PORT         = 3306
DB_NAME         = "superstore"
DB_USER         = "admin"
DB_PASSWORD     = os.environ.get("DB_PASSWORD")

# ─── STEP 1: READ RAW CSV FROM S3 ─────────────────────────────────────────────
def read_from_s3() -> pd.DataFrame:
    """Read the raw CSV directly from S3 into a DataFrame — no local file needed."""
    s3_client = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )
    obj      = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_RAW_KEY)
    body     = obj["Body"].read().decode("latin-1")
    df       = pd.read_csv(StringIO(body))
    print(f"✅ Read {df.shape[0]} rows from S3")
    return df

# ─── STEP 2: CLEAN THE DATA ───────────────────────────────────────────────────
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise column names, fix data types, handle nulls.
    Every decision here is intentional — we can explain each one in an interview.
    """
    # Standardise column names: lowercase, replace spaces with underscores
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(" ", "_")
          .str.replace("-", "_")
    )

    # Parse dates — tell Pandas the exact format so it doesn't guess wrong
    df["order_date"] = pd.to_datetime(df["order_date"], format="%d/%m/%Y", errors='coerce')
    df["ship_date"]  = pd.to_datetime(df["ship_date"],  format="%d/%m/%Y", errors='coerce')

    # Derive useful columns
    df["days_to_ship"]   = (df["ship_date"] - df["order_date"]).dt.days
    df["order_year"]     = df["order_date"].dt.year
    df["order_month"]    = df["order_date"].dt.month
    df["order_month_name"] = df["order_date"].dt.strftime("%B")  # e.g. "January"
    df["order_quarter"]  = df["order_date"].dt.quarter

    # Standardise strings: strip whitespace, title case
    for col in ["segment", "region", "category", "sub_category", "ship_mode"]:
        df[col] = df[col].str.strip().str.title()

    # Round financial columns to 2 decimal places
    for col in ["sales", "discount", "profit"]:
        df[col] = df[col].round(2)

    # Derive profit margin (avoid division by zero)
    df["profit_margin"] = np.where(
        df["sales"] != 0,
        (df["profit"] / df["sales"] * 100).round(2),
        0
    )

    # Drop duplicates (using order_id + product as unique key)
    before = df.shape[0]
    df.drop_duplicates(subset=["order_id", "product_id"], inplace=True)
    print(f"✅ Removed {before - df.shape[0]} duplicates")

    print(f"✅ Cleaned data: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

# ─── STEP 3: BUILD DIMENSION TABLES ───────────────────────────────────────────
def build_dimensions(df: pd.DataFrame) -> dict:
    """
    Extract dimension tables from the flat CSV.
    Each dimension gets a surrogate key (integer ID) — cleaner than using raw strings as FKs.
    """

    # dim_customer
    dim_customer = (
        df[["customer_id", "customer_name", "segment"]]
        .drop_duplicates(subset=["customer_id"])
        .reset_index(drop=True)
    )
    dim_customer.insert(0, "customer_key", range(1, len(dim_customer) + 1))

    # dim_product
    dim_product = (
        df[["product_id", "product_name", "category", "sub_category"]]
        .drop_duplicates(subset=["product_id"])
        .reset_index(drop=True)
    )
    dim_product.insert(0, "product_key", range(1, len(dim_product) + 1))

    # dim_location
    dim_location = (
        df[["country", "city", "state", "postal_code", "region"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_location.insert(0, "location_key", range(1, len(dim_location) + 1))

    # dim_date — one row per unique order date
    dim_date = (
        df[["order_date", "order_year", "order_month", "order_month_name", "order_quarter"]]
        .drop_duplicates(subset=["order_date"])
        .sort_values("order_date")
        .reset_index(drop=True)
    )
    dim_date.insert(0, "date_key", range(1, len(dim_date) + 1))

    print(f"✅ Dimensions built: "
          f"{len(dim_customer)} customers, "
          f"{len(dim_product)} products, "
          f"{len(dim_location)} locations, "
          f"{len(dim_date)} dates")

    return {
        "dim_customer": dim_customer,
        "dim_product":  dim_product,
        "dim_location": dim_location,
        "dim_date":     dim_date
    }

# ─── STEP 4: BUILD FACT TABLE ─────────────────────────────────────────────────
def build_fact_table(df: pd.DataFrame, dims: dict) -> pd.DataFrame:
    """
    The fact table stores one row per order line item.
    It holds measures (sales, profit, quantity) and foreign keys to dimensions.
    """
    fact = df[[
        "order_id", "order_date", "customer_id",
        "product_id", "city", "state", "postal_code",
        "ship_mode", "sales", "quantity", "discount",
        "profit", "profit_margin", "days_to_ship"
    ]].copy()

    # Join surrogate keys from dimensions
    fact = fact.merge(
        dims["dim_customer"][["customer_id", "customer_key"]],
        on="customer_id", how="left"
    )
    fact = fact.merge(
        dims["dim_product"][["product_id", "product_key"]],
        on="product_id", how="left"
    )
    fact = fact.merge(
        dims["dim_location"][["city", "state", "postal_code", "location_key"]],
        on=["city", "state", "postal_code"], how="left"
    )
    fact = fact.merge(
        dims["dim_date"][["order_date", "date_key"]],
        on="order_date", how="left"
    )

    # Keep only FK columns + measures in the final fact table
    fact_table = fact[[
        "order_id", "date_key", "customer_key", "product_key", "location_key",
        "ship_mode", "sales", "quantity", "discount", "profit",
        "profit_margin", "days_to_ship"
    ]]

    print(f"✅ Fact table built: {len(fact_table)} rows")
    return fact_table

# ─── STEP 5: LOAD INTO MYSQL ──────────────────────────────────────────────────
def load_to_mysql(dims: dict, fact_table: pd.DataFrame) -> None:
    """
    Load all tables into RDS MySQL using SQLAlchemy.
    if_exists='replace' drops and recreates the table each run — fine for development.
    In production you'd use 'append' with upsert logic.
    """
    connection_string = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(connection_string)

    # Create database if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
    
    # Reconnect to the specific database
    engine = create_engine(f"{connection_string}")

    # Load dimension tables first (fact table has FKs pointing to them)
    for table_name, df_dim in dims.items():
        df_dim.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f"✅ Loaded {table_name}: {len(df_dim)} rows")

    # Load fact table last
    fact_table.to_sql("fact_orders", engine, if_exists="replace", index=False)
    print(f"✅ Loaded fact_orders: {len(fact_table)} rows")

    print("\n🎉 All tables loaded into MySQL successfully")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("── Superstore Transform Pipeline ──\n")
    df         = read_from_s3()
    df         = clean_data(df)
    dims       = build_dimensions(df)
    fact_table = build_fact_table(df, dims)
    load_to_mysql(dims, fact_table)