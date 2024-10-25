import json,os
import boto3
from base64 import b64decode
import psycopg2

ybhost = os.environ["YBHOST"]
ybuser = os.environ["YBUSER"]
ybpassword = os.environ["YBPASSWORD"]
ybdb = os.environ["YBDATABASE"]
ybexternallocation = os.environ["YBEXTERNALLOCATION"]
ybexternalformat = os.environ["YBEXTERNALFORMAT"]

s3_client = boto3.client("s3")

def lambda_handler(event, context):
    print(f'Received event {str(event)}')
    S3_BUCKET = event['Records'][0]['s3']['bucket']['name']
    mkey = event['Records'][0]['s3']['object']['key']

    path = mkey.split('/')
    tname = path[len(path)-2]
    sname = path[len(path)-3]
     
    query_str = f"""  

    LOAD TABLE %s.%s FROM ('/%s') EXTERNAL LOCATION "%s" EXTERNAL FORMAT "%s" WITH (read_sources_concurrently 'ALLOW', num_readers '2')
                """ %  (sname,tname,mkey,ybexternallocation,ybexternalformat)   
    
    connection = psycopg2.connect(user = ybuser,
                                      password = ybpassword,
                                      host = ybhost,
                                      port = 5432,
                                      database = ybdb,
                                      application_name = "ingest")

    try:
        

        cursor = connection.cursor()
        print('connected successfully')
        
        connection.autocommit = True

        print(query_str)
        cursor.execute(query_str)
        #connection.commit()
        print('Records added successfully')

    except (Exception, psycopg2.Error) as error :
        print ("Error while connecting to PostgreSQL", error)
    finally:
        #closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
    