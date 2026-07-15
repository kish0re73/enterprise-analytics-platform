"""
etl/load.py -- LOAD stage
-------------------------------------------------------------------
Loads the transformed CSVs into the PostgreSQL star schema
(warehouse/01_star_schema.sql must be applied first). Dimensions are
loaded first and mapped from natural keys to surrogate keys before
the fact table load, which is standard warehouse-loading order.
-------------------------------------------------------------------
"""
import pandas as pd
import os
from sqlalchemy import create_engine, text

PROCESSED = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
DB_URL = os.environ.get("BI_DB_URL", "postgresql://postgres:postgres@localhost:5432/bi_warehouse")


def load():
    engine = create_engine(DB_URL)

    dim_date = pd.read_csv(f"{PROCESSED}/dim_date.csv")
    dim_customer = pd.read_csv(f"{PROCESSED}/dim_customer.csv")
    dim_product = pd.read_csv(f"{PROCESSED}/dim_product.csv")
    dim_region = pd.read_csv(f"{PROCESSED}/dim_region.csv")
    dim_channel = pd.read_csv(f"{PROCESSED}/dim_channel.csv")
    fact_sales = pd.read_csv(f"{PROCESSED}/fact_sales.csv")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE fact_sales, dim_customer, dim_product, dim_region, dim_channel, dim_date RESTART IDENTITY CASCADE;"))

    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    dim_customer.to_sql("dim_customer", engine, if_exists="append", index=False)
    dim_product.to_sql("dim_product", engine, if_exists="append", index=False)
    dim_region.to_sql("dim_region", engine, if_exists="append", index=False)
    dim_channel.to_sql("dim_channel", engine, if_exists="append", index=False)

    # map natural keys -> surrogate keys for the fact table load
    cust_map = pd.read_sql("SELECT customer_key, customer_id FROM dim_customer", engine)
    prod_map = pd.read_sql("SELECT product_key, product_id FROM dim_product", engine)
    region_map = pd.read_sql("SELECT region_key, region_id FROM dim_region", engine)
    chan_map = pd.read_sql("SELECT channel_key, channel_name FROM dim_channel", engine)

    fact = (fact_sales
            .merge(cust_map, on="customer_id", how="left")
            .merge(prod_map, on="product_id", how="left")
            .merge(region_map, on="region_id", how="left")
            .merge(chan_map, left_on="channel", right_on="channel_name", how="left"))

    fact_load = fact[["order_id", "item_id", "date_key", "customer_key", "product_key",
                       "region_key", "channel_key", "quantity", "unit_price", "discount_pct",
                       "revenue", "cost", "profit", "order_status"]]

    fact_load.to_sql("fact_sales", engine, if_exists="append", index=False, chunksize=5000)

    with engine.connect() as conn:
        counts = {t: conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                  for t in ["dim_date", "dim_customer", "dim_product", "dim_region", "dim_channel", "fact_sales"]}
    print("[LOAD] Row counts in warehouse:", counts)


if __name__ == "__main__":
    load()
