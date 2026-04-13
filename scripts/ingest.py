# ingest.py
# Purpose: Download the Superstore dataset and upload raw CSV to S3

import boto3
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────

AWS_ACCESS_KEY     = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY     = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION         = "us-east-1"
S3_BUCKET          = "superstore-analytics-bheki"  
S3_RAW_KEY         = "raw/superstore.csv"              # path inside the bucket
LOCAL_FILE         = "superstore.csv"

# ─── STEP 1: LOAD DATA ────────────────────────────────────────────────────────
def load_data(filepath: str) -> pd.DataFrame:
    """
    Load CSV into a Pandas DataFrame.
    We print shape and a preview so we can visually confirm the data loaded correctly.
    """
    df = pd.read_csv(filepath, encoding="latin-1")  # latin-1 handles special chars in names
    print(f"✅ Loaded {df.shape[0]} rows × {df.shape[1]} columns")
    print(df.head(3).to_string())
    return df

# ─── STEP 2: BASIC VALIDATION ─────────────────────────────────────────────────
def validate_data(df: pd.DataFrame) -> bool:
    """
    Run simple checks before uploading.
    In production these would be more sophisticated (Great Expectations, etc.)
    """
    required_columns = [
        "Order ID", "Order Date", "Ship Date", "Customer Name",
        "Segment", "Region", "Category", "Sub-Category",
        "Sales", "Quantity", "Discount", "Profit"
    ]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        print(f"❌ Missing columns: {missing}")
        return False

    if df.shape[0] < 1000:
        print(f"❌ Row count too low: {df.shape[0]} — file may be incomplete")
        return False

    null_pct = df.isnull().mean() * 100
    high_null = null_pct[null_pct > 20]
    if not high_null.empty:
        print(f"⚠️  High nulls detected:\n{high_null}")

    print(f"✅ Validation passed — {df.shape[0]} rows ready for upload")
    return True

# ─── STEP 3: UPLOAD TO S3 ─────────────────────────────────────────────────────
def upload_to_s3(local_path: str, bucket: str, s3_key: str) -> None:
    """
    Upload the raw CSV file to S3.
    We tag it with an upload timestamp — useful for auditing later.
    """
    s3_client = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    s3_client.upload_file(
        Filename=local_path,
        Bucket=bucket,
        Key=s3_key,
        ExtraArgs={
            "Metadata": {
                "uploaded_at": datetime.utcnow().isoformat(),
                "source": "kaggle-superstore"
            }
        }
    )
    print(f"✅ Uploaded to s3://{bucket}/{s3_key}")

# ─── STEP 4: VERIFY THE UPLOAD ────────────────────────────────────────────────
def verify_upload(bucket: str, s3_key: str) -> None:
    """
    Confirm the file exists in S3 and print its size.
    Always verify — silent failures are the hardest bugs to find.
    """
    s3_client = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    response = s3_client.head_object(Bucket=bucket, Key=s3_key)
    size_kb   = response["ContentLength"] / 1024
    print(f"✅ Verified: s3://{bucket}/{s3_key} ({size_kb:.1f} KB)")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("── Superstore Ingestion Pipeline ──")

    df = load_data(LOCAL_FILE)

    if not validate_data(df):
        raise SystemExit("Ingestion aborted — validation failed.")

    upload_to_s3(LOCAL_FILE, S3_BUCKET, S3_RAW_KEY)
    verify_upload(S3_BUCKET, S3_RAW_KEY)

    print("\n🎉 Ingestion complete. Raw data is now in S3.")