import os
from flask import Flask, request, jsonify, render_template, abort
from flask_cors import CORS, cross_origin
import simplejson as json
import boto3
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"Access-Control-Allow-Origin": "*"}})

cpustressfactor = int(os.getenv('CPUSTRESSFACTOR', 1))
memstressfactor = int(os.getenv('MEMSTRESSFACTOR', 1))
ddb_aws_region = os.getenv('DDB_AWS_REGION', 'us-east-1')
ddb_table_name = os.getenv('DDB_TABLE_NAME', 'votes')
env = os.getenv("ENV", "production")

if env == "local":
    logger.info("Usando DynamoDB local")
    ddb = boto3.resource('dynamodb', 
                         region_name=ddb_aws_region, 
                         aws_access_key_id="FAKE",
                         aws_secret_access_key="FAKE",
                         endpoint_url="http://vote-db:8000")
    

    try:

        ddbtable = ddb.Table(ddb_table_name)
        ddbtable.table_status
        logger.info(f"Tabla existente: {ddb_table_name}")
    except:
        logger.info(f"Creando tabla: {ddb_table_name}")

        ddb.create_table(
            TableName=ddb_table_name,
            KeySchema=[
                {'AttributeName': 'name', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'name', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        time.sleep(2)
        
        ddbtable = ddb.Table(ddb_table_name)
        ddbtable.put_item(Item={'name': 'cats', 'restaurantcount': 0, 'last_vote': datetime.now().isoformat()})
        ddbtable.put_item(Item={'name': 'dogs', 'restaurantcount': 0, 'last_vote': datetime.now().isoformat()})
        logger.info("Tabla inicializada con valores predeterminados")
else:
    logger.info("Usando DynamoDB en AWS")
    ddb = boto3.resource('dynamodb', region_name=ddb_aws_region)

ddbtable = ddb.Table(ddb_table_name)

logger.info(f"Factor de estrés de CPU: {cpustressfactor}")
logger.info(f"Factor de estrés de memoria: {memstressfactor}")

memeater = [0 for i in range(10000 * memstressfactor)]

def cpu_stress():
    result = 0
    for x in range(1000000 * cpustressfactor):
        result += x*x
    return result

def read_vote(entity):
    try:
        response = ddbtable.get_item(Key={'name': entity})
        normalized_response = json.dumps(response)
        json_response = json.loads(normalized_response)
        
        if 'Item' not in json_response:
            logger.warning(f"La entidad {entity} no existe en la base de datos, inicializando...")
            ddbtable.put_item(Item={
                'name': entity, 
                'restaurantcount': 0,
                'last_vote': datetime.now().isoformat()
            })
            return 0
            
        votes = json_response["Item"]["restaurantcount"]
        return int(votes)
    except Exception as e:
        logger.error(f"Error al leer votos para {entity}: {str(e)}")
        return 0

def update_vote(entity, votes):
    try:
        response = ddbtable.update_item(
            Key={'name': entity},
            UpdateExpression='SET restaurantcount = :value, last_vote = :timestamp',
            ExpressionAttributeValues={
                ':value': votes,
                ':timestamp': datetime.now().isoformat()
            },
            ReturnValues='UPDATED_NEW'
        )
        return votes
    except Exception as e:
        logger.error(f"Error al actualizar votos para {entity}: {str(e)}")
        return 0

def get_vote_history(entity, limit=10):
    try:
        response = ddbtable.get_item(Key={'name': entity})
        normalized_response = json.dumps(response)
        json_response = json.loads(normalized_response)
        
        if 'Item' not in json_response:
            return []
            
        votes = json_response["Item"]["restaurantcount"]
        last_vote = json_response["Item"].get("last_vote", datetime.now().isoformat())
        
        history = []
        for i in range(min(limit, votes)):
            history.append({
                "timestamp": last_vote,
                "count": votes - i
            })
        
        return history
    except Exception as e:
        logger.error(f"Error al obtener historial para {entity}: {str(e)}")
        return []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/cats')
def vote_cats():
    votes = read_vote("cats")
    votes += 1
    new_votes = update_vote("cats", votes)
    return str(new_votes)

@app.route('/api/dogs')
def vote_dogs():
    votes = read_vote("dogs")
    votes += 1
    new_votes = update_vote("dogs", votes)
    return str(new_votes)

@app.route('/api/getvotes')
def get_votes():
    dogs_votes = read_vote("dogs")
    cats_votes = read_vote("cats")
    
    votes_data = [
        {"name": "dogs", "value": dogs_votes},
        {"name": "cats", "value": cats_votes}
    ]
    
    return jsonify(votes_data)

@app.route('/api/getvotes/heavy')
def get_heavy_votes():
    cpu_stress()
    return get_votes()

@app.route('/api/reset', methods=['POST'])
def reset_votes():
    try:
        update_vote("dogs", 0)
        update_vote("cats", 0)
        return jsonify({"status": "success", "message": "Votos reiniciados correctamente"})
    except Exception as e:
        logger.error(f"Error al reiniciar votos: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/history/<entity>')
def get_history(entity):
    if entity not in ["dogs", "cats"]:
        abort(404, description="Entidad no encontrada")
        
    limit = request.args.get('limit', default=10, type=int)
    history = get_vote_history(entity, limit)
    
    return jsonify({
        "entity": entity,
        "history": history
    })

@app.route('/api/stats')
def get_stats():
    dogs_votes = read_vote("dogs")
    cats_votes = read_vote("cats")
    total_votes = dogs_votes + cats_votes
    
    stats = {
        "total_votes": total_votes,
        "distribution": {
            "dogs": dogs_votes / total_votes if total_votes > 0 else 0,
            "cats": cats_votes / total_votes if total_votes > 0 else 0
        },
        "leader": "dogs" if dogs_votes > cats_votes else "cats" if cats_votes > dogs_votes else "tie",
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(stats)

@app.route('/static/<path:path>')
def serve_static(path):
    return app.send_static_file(path)


@app.route('/templates/<path:path>')
def serve_template(path):
    return render_template(path)

@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Recurso no encontrado"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"status": "error", "message": "Error interno del servidor"}), 500

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    
    with open('templates/index.html', 'w') as f:
        f.write(render_template('index.html'))
    
    app.run(
        host=os.getenv('IP', '0.0.0.0'), 
        port=int(os.getenv('PORT', 8080)),
        debug=(env == "local")
    )