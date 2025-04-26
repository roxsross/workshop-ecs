import boto3
import os
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ddb_aws_region = os.getenv('DDB_AWS_REGION', 'us-east-1')
ddb_table_name = os.getenv('DDB_TABLE_NAME', 'votes')
env = os.getenv("ENV", "local")

def init_dynamodb():
    """
    Inicializa la base de datos DynamoDB con los valores predeterminados
    """
    try:
        if env == "local":
            logger.info("Configurando DynamoDB local")
            ddb = boto3.resource('dynamodb', 
                                region_name=ddb_aws_region, 
                                aws_access_key_id="FAKE",
                                aws_secret_access_key="FAKE",
                                endpoint_url="http://localhost:8000")
        else:
            logger.info("Configurando DynamoDB en AWS")
            ddb = boto3.resource('dynamodb', region_name=ddb_aws_region)
        
        # Verificar si la tabla existe
        try:
            table = ddb.Table(ddb_table_name)
            table.table_status
            logger.info(f"La tabla {ddb_table_name} ya existe.")
        except:
            logger.info(f"Creando tabla {ddb_table_name}...")
            
            # Crear la tabla
            table = ddb.create_table(
                TableName=ddb_table_name,
                KeySchema=[
                    {'AttributeName': 'name', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'name', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            
            logger.info("Esperando a que la tabla se active...")
            time.sleep(2)
            logger.info("Tabla creada correctamente.")
        
        table = ddb.Table(ddb_table_name)
        
        response_cats = table.get_item(Key={'name': 'cats'})
        response_dogs = table.get_item(Key={'name': 'dogs'})
        
        if 'Item' not in response_cats:
            logger.info("Inicializando contador para 'cats'")
            table.put_item(Item={
                'name': 'cats',
                'restaurantcount': 0,
                'last_vote': '',
                'created_at': time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        if 'Item' not in response_dogs:
            logger.info("Inicializando contador para 'dogs'")
            table.put_item(Item={
                'name': 'dogs',
                'restaurantcount': 0,
                'last_vote': '',
                'created_at': time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        logger.info("Base de datos inicializada correctamente.")
        return True
    
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {str(e)}")
        return False

if __name__ == "__main__":
    init_dynamodb()