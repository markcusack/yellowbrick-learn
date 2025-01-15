from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 8),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
}

with DAG('bitcoin_kpi_dag',
         default_args=default_args,
         schedule_interval=None,
         catchup=False) as dag:

    execute_sql_task = PostgresOperator(
        task_id='execute_sql',
        postgres_conn_id='ybconnection',  # specify your PostgreSQL connection
        sql="""
        INSERT INTO coincap_bitcoin.bitcoin_kpi (timestamp, current_price, price_change_percentage, supply, max_supply, percentage_of_max_supply_mined, volatility, moving_average_10_days, market_dominance, vwap_24_hr, vwap_crossing)
        WITH price_change_percentage_cte AS (
            SELECT 
                timestamp,
                price_usd,
                (price_usd - LAG(price_usd) OVER (ORDER BY timestamp)) / LAG(price_usd) OVER (ORDER BY timestamp) * 100 AS price_change_percentage
            FROM 
                coincap_bitcoin.bitcoin_price_tracker
        ),
        percent_mined_cte AS (
            SELECT 
                timestamp,
                supply,
                max_supply,
                supply / max_supply * 100 AS percentage_of_max_supply_mined
            FROM 
                coincap_bitcoin.bitcoin_price_tracker
            WHERE
                timestamp = (SELECT MAX(timestamp) FROM coincap_bitcoin.bitcoin_price_tracker)
        ),
        volatility_cte AS (
            SELECT 
                timestamp,
                price_usd,
                STDDEV(price_usd) OVER (ORDER BY timestamp) AS price_stddev
            FROM 
                coincap_bitcoin.bitcoin_price_tracker
        ),
        moving_average_10_days_cte AS (
            SELECT 
                timestamp,
                price_usd,
                AVG(price_usd) OVER (ORDER BY timestamp ROWS BETWEEN 2880 PRECEDING AND CURRENT ROW) AS moving_average_10_days
            FROM 
                coincap_bitcoin.bitcoin_price_tracker
        ),
        market_dominance_cte AS (
            SELECT 
                (SUM(market_cap_usd) / (SELECT SUM(market_cap_usd) FROM coincap_bitcoin.bitcoin_price_tracker)) * 100 AS market_dominance
            FROM 
                coincap_bitcoin.bitcoin_price_tracker
        ),
        vwap_crossing_cte AS (
             SELECT 
        price_usd,
        timestamp,
        bpt.vwap_24_hr,
        CASE 
            WHEN price_usd > bpt.vwap_24_hr THEN 'Above VWAP'
            WHEN price_usd < bpt.vwap_24_hr THEN 'Below VWAP'
            ELSE 'At VWAP'
        END AS vwap_crossing
    FROM 
        coincap_bitcoin.bitcoin_price_tracker bpt
        )
        SELECT 
            pc.timestamp,
            pc.price_usd AS current_price,
            pc.price_change_percentage,
            pm.supply,
            pm.max_supply,
            pm.percentage_of_max_supply_mined,
            v.price_stddev AS volatility,
            ma.price_usd AS moving_average_10_days,
            md.market_dominance,
            vc.vwap_24_hr,
            vc.vwap_crossing
        FROM 
            price_change_percentage_cte pc
        JOIN 
            percent_mined_cte pm ON pc.timestamp = pm.timestamp
        JOIN 
            volatility_cte v ON pc.timestamp = v.timestamp
        JOIN 
            moving_average_10_days_cte ma ON pc.timestamp = ma.timestamp
        CROSS JOIN 
            market_dominance_cte md
        JOIN 
            vwap_crossing_cte vc ON pc.timestamp = vc.timestamp;
        """
    )

execute_sql_task