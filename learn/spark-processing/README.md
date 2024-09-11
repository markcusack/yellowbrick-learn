# Integrate Yellowbrick and Databricks using PySpark

Databricks' Spark interface is a popular destination for landing data. Databricks also provides a native Python interface (`PySpark`) for powerful data processing and movement tasks. In this tutorial, we'll use PySpark to integrate Databricks with Yellowbrick, perform analytical transformations, and move data between the two platforms.

Here’s a quick example of a notebook (attached **here**) that can be imported into a Databricks workspace. We will run this notebook using a Yellowbrick Sandbox account (sign up for one **[here](https://cloudlabs.yellowbrick.com/trials/)**).

### Breakdown of the steps in the notebook:
1. **Step 1**: Read a million rows from the `store_sales` table in Yellowbrick.
2. **Step 2**: Perform analytical calculations in the Python interface using PySpark DataFrames.
3. **Step 3**: Write the transformed data back to Yellowbrick into a new table, `store_sales_analytics`.

**Note**: The `store_sales` table read in Step 1 can also come from a native Databricks table instead of Yellowbrick.

---

## Prerequisites for the tutorial
- A **Yellowbrick Sandbox account**.
- A **Databricks account** (regular or community edition).
- The notebook should be imported into your Databricks workspace.
  
### Here is detailed explaination of the code in the notebook:

### Import Libraries

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
import psycopg2
```
### Create a SparkSession
```python
spark = SparkSession.builder.appName("StoreSalesAnalytics").getOrCreate()
```
### Read Data from Yellowbrick

Be sure to replace the `user` and `password` to the credentials you get from your sandbox sign up.

```python
store_sales_pyspark = (spark.read.format("postgresql")
  .option("dbtable", "(SELECT * FROM tpcds_sf1000.store_sales ORDER BY ss_sold_date_sk LIMIT 1000000) AS subquery")
  .option("host", "trialsandbox.sandbox.aws.yellowbrickcloud.com")
  .option("port", "5432")
  .option("database", "sample_data")
  .option("user", "your_user")
  .option("password", "your_password")
  .load())
```
### Perform Data Transformations
```python
window = Window.partitionBy("ss_sold_date_sk", "ss_customer_sk").orderBy(desc("ss_net_profit"))
store_sales_analytics = store_sales_pyspark.select(
    "ss_sold_date_sk",
    "ss_sold_time_sk",
    "ss_item_sk",
    "ss_customer_sk",
    "ss_cdemo_sk",
    "ss_hdemo_sk",
    "ss_addr_sk",
    "ss_store_sk",
    "ss_promo_sk",
    "ss_ticket_number",
    "ss_quantity",
    "ss_wholesale_cost",
    "ss_list_price",
    "ss_sales_price",
    "ss_ext_discount_amt",
    "ss_ext_sales_price",
    "ss_ext_wholesale_cost",
    "ss_ext_list_price",
    "ss_ext_tax",
    "ss_coupon_amt",
    "ss_net_paid",
    "ss_net_paid_inc_tax",
    "ss_net_profit",
    row_number().over(window).alias("rn"),
    rank().over(window).alias("rnk"),
    dense_rank().over(window).alias("dense_rnk"),
    lead("ss_net_profit", 1).over(window).alias("next_profit"),
    lag("ss_net_profit", 1).over(window).alias("prev_profit"),
    round(col("ss_sales_price") / col("ss_list_price"), 2).alias("price_discount_pct"),
    round(col("ss_ext_sales_price") / col("ss_ext_list_price"), 2).alias("total_discount_pct"),
    round(col("ss_net_profit") / col("ss_ext_sales_price"), 2).alias("profit_margin"),
    when(col("ss_net_profit") > 0, lit(1)).otherwise(lit(0)).cast("NUMERIC").alias("profitability_status")
)
```
A window is created that partitions the data by `ss_sold_date_sk` and `ss_customer_sk`, ordering rows within each partition by `ss_net_profit` in descending order. This window is used for ranking and lead/lag functions.

The code selects key columns from the `store_sales_pyspark` DataFrame, including sales transaction details (`ss_quantity`, `ss_sales_price`, `ss_net_profit`) and various cost/price columns (`ss_wholesale_cost`, `ss_list_price`).

- `row_number()`: Adds a sequential row number (`rn`) to each row in the partition, assigning unique row numbers to each row.

- `rank()`: Computes the rank (`rnk`) of each row within its partition based on `ss_net_profit`, where rows with equal profit get the same rank.

- `dense_rank()`: Similar to `rank()` but assigns consecutive ranks (`dense_rnk`) without gaps, even if multiple rows share the same profit.

- `lead()` and `lag()`:
  - `lead()`: Creates a column (`next_profit`) showing the `ss_net_profit` value from the next row within the same partition.
  - `lag()`: Creates a column (`prev_profit`) showing the `ss_net_profit` value from the previous row in the partition.

### Discount Calculations:
- `price_discount_pct`: Calculates the percentage discount between `ss_sales_price` and `ss_list_price`, rounded to 2 decimal places.
- `total_discount_pct`: Computes the discount on extended prices (`ss_ext_sales_price` vs. `ss_ext_list_price`), also rounded to 2 decimals.

### Profit Margin:
- `profit_margin`: Calculates the profit margin as the ratio of `ss_net_profit` to `ss_ext_sales_price`, rounded to 2 decimal places.

### Profitability Status:
- Creates a binary column (`profitability_status`) indicating whether the transaction was profitable (`1` for profit, `0` for loss) based on whether `ss_net_profit` is positive or not.

### Define Yellowbrick Connection Details
Be sure to replace the `user` and `password` to the credentials you get from your sandbox sign up.

```python
driver = "org.postgresql.Driver"
database_host = "trialsandbox.sandbox.aws.yellowbrickcloud.com"
database_port = "5432"
database_name = "sample_data"
table = "tpcds_sf1000.store_sales_analytics"
user = "your_user"
password = "your_password"
```
### Construct the Postgres URL
```python
url = f"jdbc:postgresql://{database_host}:{database_port}/{database_name}?user={user}&password={password}"
```
### Create the store_sales_analytics Table in Yellowbrick
```python
create_table_query = """
CREATE TABLE IF NOT EXISTS tpcds_sf1000.store_sales_analytics (
    ss_sold_date_sk INTEGER,
    ss_sold_time_sk INTEGER,
    ss_item_sk INTEGER,
    ss_customer_sk INTEGER,
    ss_cdemo_sk INTEGER,
    ss_hdemo_sk INTEGER,
    ss_addr_sk INTEGER,
    ss_store_sk INTEGER,
    ss_promo_sk INTEGER,
    ss_ticket_number INTEGER,
    ss_quantity INTEGER,
    ss_wholesale_cost NUMERIC,
    ss_list_price NUMERIC,
    ss_sales_price NUMERIC,
    ss_ext_discount_amt NUMERIC,
    ss_ext_sales_price NUMERIC,
    ss_ext_wholesale_cost NUMERIC,
    ss_ext_list_price NUMERIC,
    ss_ext_tax NUMERIC,
    ss_coupon_amt NUMERIC,
    ss_net_paid NUMERIC,
    ss_net_paid_inc_tax NUMERIC,
    ss_net_profit NUMERIC,
    rn INTEGER,
    rnk INTEGER,
    dense_rnk INTEGER,
    next_profit NUMERIC,
    prev_profit NUMERIC,
    price_discount_pct NUMERIC,
    total_discount_pct NUMERIC,
    profit_margin NUMERIC,
    profitability_status NUMERIC
) Distribute random;
"""
```
### Execute the create table command using psycopg2
```python
conn = psycopg2.connect(host=database_host, port=database_port, dbname=database_name, user=user, password=password)
cursor = conn.cursor()
cursor.execute(create_table_query)
conn.commit()
```
### Write the DataFrame to the Table Using the Postgres Spark Connector
```python
(store_sales_analytics.write
    .format("postgresql")
    .option("host", database_host)
    .option("port", database_port)
    .option("database", database_name)
    .option("user", user)
    .option("password", password)
    .option("dbtable", table)
    .mode("append")
    .save())
```
### Execute the Count Query
```python
cursor.execute("SELECT COUNT(*) AS row_count FROM tpcds_sf1000.store_sales_analytics;")
```
### Fetch the result
```python
result = cursor.fetchone()
row_count = result[0]
```
### Output the row count
```python
print(f"Row count after insertion: {row_count}")
```
### Clean Up by Dropping the store_sales_analytics Table
```python
cursor.execute("DROP TABLE IF EXISTS tpcds_sf1000.store_sales_analytics")
conn.commit()
```
### Close cursor and connection
```python
cursor.close()
conn.close()

print("Cleanup: 'store_sales_analytics' table has been dropped.")
```