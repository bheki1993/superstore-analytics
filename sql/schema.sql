-- schema.sql
-- Run this BEFORE loading data in transform.py
-- It defines the exact structure MySQL should use

CREATE DATABASE IF NOT EXISTS superstore;
USE superstore;

-- ── DIMENSION: DATE ───────────────────────────────────────────────────────────
-- Why a date dimension? So we can filter/group by year, quarter, month
-- without running expensive date functions on every query.
CREATE TABLE IF NOT EXISTS dim_date (
    date_key        INT             NOT NULL AUTO_INCREMENT,
    order_date      DATE            NOT NULL,
    order_year      SMALLINT        NOT NULL,   -- e.g. 2023
    order_month     TINYINT         NOT NULL,   -- 1–12
    order_month_name VARCHAR(10)    NOT NULL,   -- e.g. "January"
    order_quarter   TINYINT         NOT NULL,   -- 1–4

    PRIMARY KEY (date_key),
    UNIQUE KEY uq_order_date (order_date)       -- one row per unique date
);

-- ── DIMENSION: CUSTOMER ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key    INT             NOT NULL AUTO_INCREMENT,
    customer_id     VARCHAR(20)     NOT NULL,
    customer_name   VARCHAR(100)    NOT NULL,
    segment         VARCHAR(30)     NOT NULL,   -- Consumer / Corporate / Home Office

    PRIMARY KEY (customer_key),
    UNIQUE KEY uq_customer_id (customer_id),
    INDEX idx_segment (segment)                 -- index because we filter by segment often
);

-- ── DIMENSION: PRODUCT ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_product (
    product_key     INT             NOT NULL AUTO_INCREMENT,
    product_id      VARCHAR(20)     NOT NULL,
    product_name    VARCHAR(200)    NOT NULL,
    category        VARCHAR(50)     NOT NULL,   -- Furniture / Office Supplies / Technology
    sub_category    VARCHAR(50)     NOT NULL,   -- Chairs, Phones, Binders, etc.

    PRIMARY KEY (product_key),
    UNIQUE KEY uq_product_id (product_id),
    INDEX idx_category (category),
    INDEX idx_sub_category (sub_category)
);

-- ── DIMENSION: LOCATION ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_location (
    location_key    INT             NOT NULL AUTO_INCREMENT,
    country         VARCHAR(50)     NOT NULL,
    city            VARCHAR(100)    NOT NULL,
    state           VARCHAR(100)    NOT NULL,
    postal_code     VARCHAR(20),               -- nullable: some records may lack it
    region          VARCHAR(30)     NOT NULL,   -- East / West / Central / South

    PRIMARY KEY (location_key),
    INDEX idx_region (region),
    INDEX idx_state (state)
);

-- ── FACT TABLE: ORDERS ────────────────────────────────────────────────────────
-- One row per order line item (one product in one order)
-- Stores measures (sales, profit) + FK references to all dimensions
CREATE TABLE IF NOT EXISTS fact_orders (
    fact_id         INT             NOT NULL AUTO_INCREMENT,
    order_id        VARCHAR(30)     NOT NULL,   -- natural key from source
    date_key        INT             NOT NULL,
    customer_key    INT             NOT NULL,
    product_key     INT             NOT NULL,
    location_key    INT             NOT NULL,
    ship_mode       VARCHAR(30)     NOT NULL,

    -- Measures (the numbers we actually analyse)
    sales           DECIMAL(10,2)   NOT NULL,
    quantity        TINYINT         NOT NULL,
    discount        DECIMAL(4,2)    NOT NULL,   -- e.g. 0.20 = 20% discount
    profit          DECIMAL(10,2)   NOT NULL,   -- can be negative (loss)
    profit_margin   DECIMAL(6,2)    NOT NULL,   -- pre-calculated % for speed
    days_to_ship    TINYINT         NOT NULL,

    PRIMARY KEY (fact_id),

    -- Foreign key constraints enforce referential integrity
    CONSTRAINT fk_date      FOREIGN KEY (date_key)     REFERENCES dim_date(date_key),
    CONSTRAINT fk_customer  FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    CONSTRAINT fk_product   FOREIGN KEY (product_key)  REFERENCES dim_product(product_key),
    CONSTRAINT fk_location  FOREIGN KEY (location_key) REFERENCES dim_location(location_key),

    -- Indexes on FK columns make JOINs dramatically faster
    INDEX idx_date_key     (date_key),
    INDEX idx_customer_key (customer_key),
    INDEX idx_product_key  (product_key),
    INDEX idx_location_key (location_key),
    INDEX idx_order_id     (order_id)
);