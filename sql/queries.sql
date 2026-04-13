-- ── 1. TOTAL REVENUE, PROFIT & ORDERS (top-level KPI cards) ──────────────────
SELECT
    ROUND(SUM(sales), 2)                          AS total_revenue,
    ROUND(SUM(profit), 2)                         AS total_profit,
    COUNT(DISTINCT order_id)                      AS total_orders,
    ROUND(AVG(sales), 2)                          AS avg_order_value,
    ROUND(SUM(profit) / SUM(sales) * 100, 2)      AS overall_margin_pct
FROM fact_orders;


-- ── 2. MONTHLY REVENUE TREND (line chart) ────────────────────────────────────
SELECT
    d.order_year,
    d.order_month,
    d.order_month_name,
    ROUND(SUM(f.sales), 2)   AS monthly_revenue,
    ROUND(SUM(f.profit), 2)  AS monthly_profit,
    COUNT(DISTINCT f.order_id) AS monthly_orders
FROM fact_orders f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.order_year, d.order_month, d.order_month_name
ORDER BY d.order_year, d.order_month;


-- ── 3. REVENUE BY CATEGORY (bar chart) ───────────────────────────────────────
SELECT
    p.category,
    ROUND(SUM(f.sales), 2)                        AS revenue,
    ROUND(SUM(f.profit), 2)                       AS profit,
    ROUND(SUM(f.profit) / SUM(f.sales) * 100, 2) AS margin_pct,
    COUNT(DISTINCT f.order_id)                    AS orders
FROM fact_orders f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category
ORDER BY revenue DESC;


-- ── 4. TOP 10 SUB-CATEGORIES BY REVENUE ──────────────────────────────────────
SELECT
    p.sub_category,
    p.category,
    ROUND(SUM(f.sales), 2)   AS revenue,
    ROUND(SUM(f.profit), 2)  AS profit
FROM fact_orders f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.sub_category, p.category
ORDER BY revenue DESC
LIMIT 10;


-- ── 5. REVENUE BY REGION (map / bar chart) ───────────────────────────────────
SELECT
    l.region,
    ROUND(SUM(f.sales), 2)                        AS revenue,
    ROUND(SUM(f.profit), 2)                       AS profit,
    ROUND(SUM(f.profit) / SUM(f.sales) * 100, 2) AS margin_pct,
    COUNT(DISTINCT f.order_id)                    AS orders
FROM fact_orders f
JOIN dim_location l ON f.location_key = l.location_key
GROUP BY l.region
ORDER BY revenue DESC;


-- ── 6. CUSTOMER SEGMENT BREAKDOWN (pie chart) ────────────────────────────────
SELECT
    c.segment,
    ROUND(SUM(f.sales), 2)                        AS revenue,
    COUNT(DISTINCT f.order_id)                    AS orders,
    ROUND(SUM(f.profit) / SUM(f.sales) * 100, 2) AS margin_pct
FROM fact_orders f
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.segment
ORDER BY revenue DESC;


-- ── 7. YEAR-OVER-YEAR GROWTH ──────────────────────────────────────────────────
SELECT
    d.order_year,
    ROUND(SUM(f.sales), 2) AS annual_revenue,
    ROUND(
        (SUM(f.sales) - LAG(SUM(f.sales)) OVER (ORDER BY d.order_year))
        / LAG(SUM(f.sales)) OVER (ORDER BY d.order_year) * 100
    , 2) AS yoy_growth_pct
FROM fact_orders f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.order_year
ORDER BY d.order_year;


-- ── 8. MOST PROFITABLE PRODUCTS ───────────────────────────────────────────────
SELECT
    p.product_name,
    p.category,
    ROUND(SUM(f.profit), 2)  AS total_profit,
    ROUND(SUM(f.sales), 2)   AS total_revenue
FROM fact_orders f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_name, p.category
ORDER BY total_profit DESC
LIMIT 10;