"""
etl/extract.py -- EXTRACT stage
-------------------------------------------------------------------
Simulates pulling data from operational source systems (an orders DB,
a product catalog, a CRM) into a raw landing zone. No source dataset
was provided for this task, so this generates a realistic one with
genuine seasonality, a repeat-customer pattern, and simulated
inventory -- the same approach used in prior tasks, scaled up here.
-------------------------------------------------------------------
"""
import numpy as np
import pandas as pd
from faker import Faker
import random
import os

SEED = 42
np.random.seed(SEED)
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUT, exist_ok=True)

regions = pd.DataFrame([
    {"region_id": 1, "region_name": "North", "country": "India"},
    {"region_id": 2, "region_name": "South", "country": "India"},
    {"region_id": 3, "region_name": "East", "country": "India"},
    {"region_id": 4, "region_name": "West", "country": "India"},
    {"region_id": 5, "region_name": "Central", "country": "India"},
])
REGION_W = [0.22, 0.30, 0.16, 0.20, 0.12]

CATEGORIES = {
    "Electronics": (2000, 45000, 0.22), "Home & Kitchen": (400, 9000, 0.35),
    "Fashion": (250, 6000, 0.40), "Beauty": (150, 2500, 0.45),
    "Sports": (300, 7000, 0.32), "Books": (120, 1500, 0.28),
}
products, pid = [], 1
for cat, (low, high, margin) in CATEGORIES.items():
    n = {"Electronics": 18, "Home & Kitchen": 16, "Fashion": 20, "Beauty": 14, "Sports": 12, "Books": 10}[cat]
    for _ in range(n):
        sell = round(float(np.random.triangular(low, low + (high-low)*0.3, high)), 2)
        cost = round(sell * (1 - margin - np.random.uniform(-0.05, 0.05)), 2)
        products.append({"product_id": pid, "product_name": f"{cat.split()[0]} {fake.word().capitalize()} {pid}",
                          "category": cat, "cost_price": cost, "sell_price": sell,
                          "current_stock": int(np.random.randint(0, 500)),
                          "reorder_level": int(np.random.randint(30, 100))})
        pid += 1
products = pd.DataFrame(products)

N_CUSTOMERS = 800
start_date, end_date = pd.Timestamp("2023-07-01"), pd.Timestamp("2026-06-30")
span_days = (end_date - start_date).days
customers = []
for cid in range(1, N_CUSTOMERS + 1):
    signup = start_date + pd.Timedelta(days=int(np.random.triangular(0, 0, span_days)))
    region_id = int(np.random.choice(regions["region_id"], p=REGION_W))
    customers.append({"customer_id": cid, "customer_name": fake.name(), "email": fake.email(),
                       "signup_date": signup.strftime("%Y-%m-%d"), "region_id": region_id, "city": fake.city()})
customers = pd.DataFrame(customers)

CHANNELS = ["Online", "Retail Store", "Wholesale"]
CHANNEL_W = [0.58, 0.30, 0.12]
STATUSES = ["Completed", "Completed", "Completed", "Completed", "Cancelled", "Returned"]

loyal_pool = list(customers.sample(frac=0.18, random_state=3)["customer_id"])
casual_pool = list(customers[~customers["customer_id"].isin(loyal_pool)]["customer_id"])
all_days = pd.date_range(start_date, end_date, freq="D")

def seasonal_weight(date):
    w = 1.0
    if date.month == 11: w = 1.5
    elif date.month == 12: w = 1.3
    elif date.month == 6: w = 1.25
    elif date.month == 2: w = 0.8
    months = (date.year - start_date.year) * 12 + (date.month - start_date.month)
    w *= (1 + 0.012 * months)
    return w

day_w = np.array([seasonal_weight(d) for d in all_days])
day_p = day_w / day_w.sum()

orders, order_items = [], []
order_id, item_id = 1, 1
N_ORDERS = 15000
product_ids = products["product_id"].values
product_prices = products.set_index("product_id")["sell_price"].to_dict()

for _ in range(N_ORDERS):
    is_loyal = random.random() < 0.55
    customer_id = random.choice(loyal_pool) if is_loyal else random.choice(casual_pool)
    cust_signup = pd.Timestamp(customers.loc[customers.customer_id == customer_id, "signup_date"].values[0])
    valid_days = all_days[all_days >= cust_signup]
    if len(valid_days) == 0:
        continue
    vw = day_w[all_days >= cust_signup]
    vp = vw / vw.sum()
    order_date = pd.Timestamp(np.random.choice(valid_days, p=vp))

    region_id = int(customers.loc[customers.customer_id == customer_id, "region_id"].values[0])
    channel = np.random.choice(CHANNELS, p=CHANNEL_W)
    status = random.choice(STATUSES)
    orders.append({"order_id": order_id, "customer_id": customer_id, "order_date": order_date.strftime("%Y-%m-%d"),
                    "region_id": region_id, "channel": channel, "status": status})

    n_items = np.random.choice([1, 1, 2, 2, 3, 4], p=[0.35, 0.25, 0.2, 0.1, 0.06, 0.04])
    chosen = np.random.choice(product_ids, size=n_items, replace=False)
    for prod_id in chosen:
        qty = int(np.random.choice([1, 1, 2, 3], p=[0.55, 0.2, 0.15, 0.1]))
        unit_price = product_prices[prod_id]
        discount = float(np.random.choice([0, 0, 0, 5, 10, 15], p=[0.5, 0.15, 0.1, 0.12, 0.08, 0.05]))
        order_items.append({"item_id": item_id, "order_id": order_id, "product_id": int(prod_id),
                             "quantity": qty, "unit_price": unit_price, "discount_pct": discount})
        item_id += 1
    order_id += 1

orders = pd.DataFrame(orders)
order_items = pd.DataFrame(order_items)

regions.to_csv(f"{OUT}/regions.csv", index=False)
products.to_csv(f"{OUT}/products.csv", index=False)
customers.to_csv(f"{OUT}/customers.csv", index=False)
orders.to_csv(f"{OUT}/orders.csv", index=False)
order_items.to_csv(f"{OUT}/order_items.csv", index=False)

print(f"[EXTRACT] customers={len(customers)} products={len(products)} regions={len(regions)} "
      f"orders={len(orders)} order_items={len(order_items)}")
print(f"[EXTRACT] Total raw records: {len(customers)+len(products)+len(regions)+len(orders)+len(order_items)}")
