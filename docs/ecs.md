
```markdown
# Despliegue de la Aplicación de Votación en ECS Fargate y DynamoDB

Esta guía te guiará para desplegar la aplicación de votación utilizando **Amazon ECS Fargate** como orquestador de contenedores y **Amazon DynamoDB** como recurso de base de datos.

## Requisitos Previos

Antes de desplegar la aplicación, asegúrate de tener lo siguiente:

- **AWS CLI**: Para interactuar con los servicios de AWS.
- **AWS Account**: Necesitarás tener una cuenta de AWS activa.
- **Docker**: Para construir y enviar imágenes a Amazon ECR.
- **AWS Elastic Container Registry (ECR)**: Para almacenar la imagen del contenedor de la aplicación.
- **Amazon ECS Fargate**: Para ejecutar los contenedores en un entorno sin servidor.
- **IAM Role**: Para gestionar los permisos necesarios en ECS y DynamoDB.

## Pasos para Desplegar la Aplicación

### 1. Crear la Imagen del Contenedor

Lo primero que debes hacer es crear la imagen del contenedor de la aplicación para subirla a **Amazon ECR**.

1. **Construir la Imagen Docker**:

   Asegúrate de estar en el directorio raíz de tu aplicación (donde está el archivo `Dockerfile`).

   Ejecuta el siguiente comando para construir la imagen:

   ```bash
   docker build -t voting-app .
   ```

2. **Autenticarse en Amazon ECR**:

   Si aún no has configurado tu CLI de AWS, ejecuta:

   ```bash
   aws configure
   ```

   Luego, autentícate en ECR para poder empujar la imagen:

   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com
   ```

3. **Crear un Repositorio en Amazon ECR**:

   Crea un repositorio en ECR donde almacenarás la imagen:

   ```bash
   aws ecr create-repository --repository-name voting-app --region us-east-1 
   ```

4. **Etiquetar y Subir la Imagen a ECR**:

   Etiqueta la imagen con el URI de tu repositorio en ECR y sube la imagen:

   ```bash
   docker tag voting-app:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/voting-app:latest
   docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/voting-app:latest
   ```

### 2. Crear la Tabla DynamoDB

1. **Crear la Tabla en DynamoDB**:

   Crea una tabla en DynamoDB con el nombre `votes` (o cualquier nombre que desees). Puedes hacerlo desde la consola de AWS o mediante el siguiente comando de AWS CLI:

   ```bash
    aws dynamodb create-table \
    --table-name votes \
    --attribute-definitions \
        AttributeName=name,AttributeType=S \
    --key-schema \
        AttributeName=name,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1

   ```
2. **Agregar Ítems a la Tabla DynamoDB**:

   Para agregar elementos (votos) a la tabla `votes`, puedes usar el siguiente comando para insertar algunos ítems de ejemplo:

   ```bash
    aws dynamodb put-item \
    --table-name votes \
    --item "{
        \"name\": {\"S\": \"cats\"},
        \"restaurantcount\": {\"N\": \"0\"},
        \"last_vote\": {\"S\": \"\"},
        \"created_at\": {\"S\": \"$(date +%Y-%m-%d\ %H:%M:%S)\"}
    }" \
    --region us-east-1



    aws dynamodb put-item \
    --table-name votes \
    --item "{
        \"name\": {\"S\": \"dogs\"},
        \"restaurantcount\": {\"N\": \"0\"},
        \"last_vote\": {\"S\": \"\"},
        \"created_at\": {\"S\": \"$(date +%Y-%m-%d\ %H:%M:%S)\"}
    }" \
    --region us-east-1


   ```
   
3. **Configurar las Credenciales**:

   Asegúrate de que tu aplicación esté configurada para acceder a DynamoDB utilizando las credenciales adecuadas, o usa roles de IAM en ECS Fargate para obtener acceso a DynamoDB.

### 3. Crear una Política IAM

La aplicación necesitará permisos para interactuar con DynamoDB. Para ello, debes crear una política IAM y asignarla a un rol de ECS.

1. **Crear la Política IAM**:

   Crea una política de permisos para que ECS pueda interactuar con DynamoDB. Guarda el siguiente documento JSON como `dynamo-policy.json`:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:UpdateItem"
            ],
            "Resource": "arn:aws:dynamodb:us-east-1:<aws_account_id>:table/votes"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:us-east-1:<aws_account_id>:log-group:/ecs/voting-app:*"
        }
    ]
}
```
   ```

   Aplica esta política con el siguiente comando:

   ```bash
   aws iam create-policy --policy-name DynamoDBVotingPolicy --policy-document file://dynamo-policy.json --region us-east-1
   ```

2. **Crear el Role IAM para ECS**:

   Crea un rol de IAM para ECS que permita a Fargate acceder a DynamoDB. Usa el siguiente comando para crear el rol y asociar la política que acabas de crear:

   ```bash
   aws iam create-role \
     --role-name ecs-task-role \
     --assume-role-policy-document file://ecs-trust-policy.json \
     --region us-east-1
   ```

   **Archivo `ecs-trust-policy.json`**:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Service": "ecs-tasks.amazonaws.com"
         },
         "Action": "sts:AssumeRole"
       }
     ]
   }
   ```

3. **Asociar la Política al Rol**:

   Asocia la política de DynamoDB al rol `ecs-task-role`:

   ```bash
   aws iam attach-role-policy \
     --role-name ecs-task-role \
     --policy-arn arn:aws:iam::<aws_account_id>:policy/DynamoDBVotingPolicy \
     --region us-east-1
   ```

### 3. Crear una Definición de Tarea en ECS

1. **Crear el Role de IAM para ECS**:

   Crea un rol de IAM que permita a ECS acceder a los recursos necesarios, como DynamoDB y CloudWatch para logs.

2. **Crear la Definición de Tarea**:

   Crea una definición de tarea en ECS que utilice la imagen de Docker que subiste a ECR. Aquí hay un ejemplo básico de cómo hacerlo:

   ```json
   {
     "family": "voting-app-task",
     "networkMode": "awsvpc",
     "containerDefinitions": [
       {
         "name": "voting-app-container",
         "image": "<aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/voting-app:latest",
         "essential": true,
         "memory": 512,
         "cpu": 256,
         "environment": [
           {
             "name": "DDB_AWS_REGION",
             "value": "us-east-1"
           },
           {
             "name": "DDB_TABLE_NAME",
             "value": "votes"
           },
           {
             "name": "ENV",
             "value": "production"
           }
         ],
         "portMappings": [
           {
             "containerPort": 8080,
             "hostPort": 8080
           }
         ]
       }
     ]
   }
   ```

   Guarda este archivo como `task-definition.json` y luego registra la definición de tarea con el siguiente comando:

   ```bash
   aws ecs register-task-definition --cli-input-json file://task-definition.json
   ```

### 4. Crear el Clúster ECS

1. **Crear un Clúster ECS con Fargate**:

   Desde la consola de ECS, crea un nuevo clúster ECS de tipo "Fargate". Selecciona la red y las subredes necesarias para tu clúster.

   También puedes hacerlo desde AWS CLI:

   ```bash
   aws ecs create-cluster --cluster-name voting-app-cluster --region us-east-1
   ```

### 5. Desplegar la Tarea en Fargate

1. **Ejecutar la Tarea en Fargate**:

   Después de crear la definición de tarea y el clúster, ejecuta la tarea en Fargate:

   ```bash
   aws ecs run-task \
     --cluster voting-app-cluster \
     --task-definition voting-app-task \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
     --region us-east-1
   ```

   Asegúrate de reemplazar `subnet-xxxxx` y `sg-xxxxx` con tus propias subredes y grupos de seguridad.

### 6. Configurar un Load Balancer (Opcional)

Si deseas exponer tu aplicación a través de un balanceador de carga, configura un **Application Load Balancer (ALB)** para dirigir el tráfico HTTP a tu servicio en Fargate. Asegúrate de que el contenedor esté configurado para aceptar tráfico en el puerto 8080.

1. **Crear un ALB** y **Configurar el Target Group**.

2. **Asociar el ALB con el servicio de ECS**.

### 7. Probar la Aplicación

Una vez que la tarea esté en ejecución, puedes acceder a la aplicación a través de la URL pública del Load Balancer (si lo configuraste) o la IP pública de la instancia de Fargate (si no usaste un ALB).

Accede a:

```bash
http://<load-balancer-dns-name>
```

## Conclusión

¡Ahora tienes tu aplicación desplegada en **Amazon ECS Fargate** con **DynamoDB** como base de datos! Puedes interactuar con la aplicación de votación a través del balanceador de carga o directamente desde la IP pública del servicio en Fargate.
