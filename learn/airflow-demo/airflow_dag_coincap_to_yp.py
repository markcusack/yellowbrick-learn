from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from datetime import datetime, timedelta
import pytz
import requests
import pandas as pd
from airflow.hooks.postgres_hook import PostgresHook

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 8),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
}

def fetch_and_upload_bitcoin_price():
    api_url = 'https://api.coincap.io/v2/assets/bitcoin'
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()

        # Get the current time in Eastern Standard Time (EST)
        est_tz = pytz.timezone('US/Eastern')
        timestamp = datetime.now(est_tz).strftime('%Y-%m-%d %H:%M:%S')

        # Extract relevant data from the API response
        relevant_data = {
            'id': (data['data']['id']),
            'timestamp': timestamp,
            'rank': int(data['data']['rank']),
            'symbol': data['data']['symbol'],
            'name': data['data']['name'],
            'supply': float(data['data']['supply']),
            'max_supply': float(data['data']['maxSupply']),
            'market_cap_usd': float(data['data']['marketCapUsd']),
            'volume_usd_24_hr': float(data['data']['volumeUsd24Hr']),
            'price_usd': float(data['data']['priceUsd']),
            'change_percent_24_hr': float(data['data']['changePercent24Hr']),
            'vwap_24_hr': float(data['data']['vwap24Hr']),
            'explorer': data['data']['explorer']
        }

        # Convert the relevant data to a DataFrame
        df = pd.DataFrame(relevant_data, index=[0])

        # Get Postgres connection
        hook = PostgresHook(postgres_conn_id='ybconnection')

        # Insert DataFrame into destination table
        hook.insert_rows(table='coincap_bitcoin.bitcoin_price_tracker', rows=df.values.tolist())

    else:
        raise Exception('Unable to fetch Bitcoin price from CoinCap API')

with DAG('coincaptoyb_dag',
         default_args=default_args,
         schedule_interval='*/5 * * * *',  # Run every 5 minutes
         catchup=False) as dag:
    
    # Define the child DAG to trigger
    child_dag_id = 'bitcoin_kpi_dag'

    # Define the TriggerDagRunOperator to trigger the child DAG
    trigger_child_dag = TriggerDagRunOperator(
        task_id='execute_sql_task',
        trigger_dag_id=child_dag_id,
        execution_date="{{ execution_date }}",
        dag=dag,
    )



    fetch_and_upload_task = PythonOperator(
        task_id='fetch_and_upload_bitcoin_price',
        python_callable=fetch_and_upload_bitcoin_price
    )
    fetch_and_upload_task >> trigger_child_dag
