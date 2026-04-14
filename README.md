# Superstore Sales Analytics — AWS Data Pipeline & Dashboard

> A end-to-end cloud data pipeline built on AWS, transforming raw retail 
> transaction data into an interactive business intelligence dashboard.

![Dashboard Preview](docs/dashboard_preview.png)

## 🔗 Live Dashboard
**URL:** http://3.236.12.118:8088/superset/dashboard/p/jB4xKrr8KZb/  
**Username:** viewer  
**Password:** demo1234  

---

## 📋 Project Overview

### Problem Statement
A retail business collects thousands of daily transactions across multiple 
regions and product categories but has no centralised way to monitor 
performance. Business teams cannot quickly answer questions like:
- Which regions are underperforming?
- What product categories drive the most profit?
- Are monthly sales trending up or down?

### Solution
A fully automated cloud data pipeline that ingests raw sales data, transforms 
it into a structured data warehouse, and surfaces insights through an 
interactive dashboard — enabling self-serve analytics for business users.

### Key Insights Uncovered
- Technology drives the highest revenue (~36% of total sales)
- The West region consistently outperforms all others
- Q4 shows a strong seasonal spike across all categories
- Tables and Bookcases have negative profit margins despite high sales volume

---

## 🏗️ Architecture

![Architecture Diagram](docs\architecture.png)

### Data Flow
- Kaggle CSV → Amazon S3 (raw) → Python/Pandas (transform) → Amazon RDS MySQL (warehouse) → Apache Superset (dashboard)

### AWS Services Used

| Service | Purpose |
|---------|---------|
| Amazon S3 | Raw data lake — stores original untransformed CSV |
| Amazon RDS (MySQL) | Managed relational database — star schema warehouse |
| Amazon EC2 | Hosts Apache Superset and runs pipeline scripts |

---

## 🗄️ Database Design

Star schema with one fact table and four dimension tables:

fact_orders (centre)
├── dim_date        (when the order occurred)
├── dim_customer    (who placed the order)
├── dim_product     (what was ordered)
└── dim_location    (where it was shipped)

### Why Star Schema?
- Dimension tables eliminate data redundancy
- Flat fact table makes aggregation queries fast
- Industry-standard pattern for analytical workloads
- Maps naturally to dashboard filter dimensions

---

## 📊 Dashboard KPIs

| KPI | Value |
|-----|-------|
| Total Revenue | ~$2.3M |
| Total Profit | ~$286K |
| Total Orders | ~5,009 |

### Charts Included
- Monthly revenue and profit trend (line chart)
- Revenue by product category (bar chart)
- Revenue by region (horizontal bar chart)
- Customer segment breakdown (pie chart)
- Interactive filters: date range, category, region, segment

---

## ⚙️ Technical Stack

| Layer | Technology |
|-------|-----------|
| Data ingestion | Python, boto3, Pandas |
| Data storage | Amazon S3 |
| Data warehouse | Amazon RDS — MySQL |
| Data transformation | Python, Pandas, SQLAlchemy |
| Visualisation | Apache Superset 6.0.0 |
| Infrastructure | Amazon EC2 (Ubuntu 22.04) |
| Version control | Git, GitHub |

---

## 🚀 How to Run This Project

### Prerequisites
- AWS account with S3, RDS, and EC2 access
- Python 3.10+
- MySQL client

### 1. Clone the Repository
```bash
git clone https://github.com/bheki1993/superstore-analytics.git
cd superstore-analytics
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your actual AWS and database credentials
```

### 4. Set Up AWS Infrastructure
- Create an S3 bucket
- Launch an RDS MySQL instance
- Launch an EC2 instance (Ubuntu 22.04, t2.medium)

### 5. Run the Pipeline
```bash
# Step 1: Ingest raw data to S3
python scripts/ingest.py

# Step 2: Transform and load into MySQL
python scripts/transform.py

# Step 3: Create database schema
mysql -h your-rds-endpoint -u admin -p superstore < sql/schema.sql
```

### 6. Set Up Superset
```bash
# Install and initialise Superset
pip install apache-superset==6.0.0
superset db upgrade
superset fab create-admin
superset init
superset run -h 0.0.0.0 -p 8088 --with-threads
```

### 7. Import the Dashboard
- Go to Dashboards → Import Dashboard
- Upload `dashboard/superstore_dashboard.json`

---

## 📁 Repository Structure

superstore-analytics/
├── README.md
├── requirements.txt
├── .env.example
├── scripts/
│   ├── ingest.py          # S3 ingestion pipeline
│   └── transform.py       # Data cleaning and RDS loading
├── sql/
│   ├── schema.sql          # Star schema table definitions
│   └── queries.sql         # KPI and dashboard queries
├── docs/
│   ├── architecture.png
│   └── dashboard_preview.png
└── dashboard/
└── superstore_dashboard.json

---

## 💡 Key Technical Decisions

**Why S3 for raw storage?**
Separating raw and processed data follows the data lake pattern used at 
scale. If the transform script corrupts data, the original is always 
recoverable from S3.

**Why a star schema over a flat table?**
Star schemas eliminate redundancy in dimension data, make JOIN logic 
predictable, and allow Superset filters to map cleanly to dimension columns. 
The query performance difference becomes significant at scale.

**Why pre-calculate profit_margin in the fact table?**
Dashboard queries run on every page load. Pre-computing derived metrics at 
load time removes runtime calculation overhead — a standard warehouse 
optimisation pattern.

**Why Apache Superset over Tableau or Power BI?**
Superset is open-source, self-hosted, and used in production at companies 
like Airbnb and Lyft. Deploying it on EC2 demonstrates cloud deployment 
skills that managed BI tools do not.

---

## 🔧 Potential Improvements

- Automate pipeline with Apache Airflow or AWS Lambda on a schedule
- Add dbt for SQL transformation layer and data testing
- Replace SQLite Superset backend with PostgreSQL for production stability
- Add Great Expectations for automated data quality checks
- Implement CDC (Change Data Capture) for incremental loads
- Add Terraform scripts to provision AWS infrastructure as code

---

## 👤 Author

Bhekumuzi Sodinga  
[LinkedIn](https://www.linkedin.com/in/bhekumuzi-sodingaa-b6473b120/) 
[GitHub](https://github.com/bheki1993)