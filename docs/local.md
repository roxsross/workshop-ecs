
```markdown
# Configuración Local de la Aplicación de Votación

Esta guía te ayudará a configurar la aplicación de votación y su entorno local.

## Requisitos Previos

Antes de ejecutar la aplicación, asegúrate de tener lo siguiente instalado en tu máquina:

- Docker: Para los servicios en contenedores.
- Docker Compose: Para gestionar aplicaciones con múltiples contenedores.
- Python 3.x: Para ejecutar la aplicación backend en Flask.
- AWS CLI (opcional): Para interactuar con DynamoDB localmente.


## Pasos para Ejecutar Localmente

### 1. Clonar el repositorio

Si aún no lo has hecho, clona el repositorio a tu máquina local:

```bash
git clone https://github.com/roxsross/workshop-ecs
cd workshop-ecs
```

### 2. Construir los Contenedores de Docker

Asegúrate de tener todos los contenedores necesarios construidos usando Docker Compose:

```bash
docker-compose build
```

### 3. Configurar el Entorno Local

Esta aplicación depende de dos servicios principales:

- **vote**: El backend basado en Flask que maneja las solicitudes y se comunica con DynamoDB.
- **vote-db**: Un servicio local de DynamoDB que corre dentro de un contenedor Docker.

Estos servicios están definidos en el archivo `docker-compose.yml`.

### 4. Configurar las Variables de Entorno

Puedes configurar las variables de entorno en el archivo `docker-compose.yml` bajo el servicio `vote`:

- `DDB_AWS_REGION`: Establece esta variable a la región de AWS que prefieras (por defecto: `us-east-1`).
- `DDB_TABLE_NAME`: El nombre de la tabla de DynamoDB a usar (por defecto: `votes`).
- `ENV`: Establece esta variable a `local` para especificar que la aplicación está ejecutándose en un entorno local.

Ejemplo de configuración:

```yaml
vote:
  build:
    context: .
    dockerfile: Dockerfile
  ports:
    - "8080:8080"
  environment:
    - DDB_AWS_REGION=us-east-1
    - DDB_TABLE_NAME=votes
    - ENV=local
  depends_on:
    - vote-db
```


### 5. Inicializar DynamoDB

El servicio `vote-db` usa un contenedor Docker que corre DynamoDB Local. Cuando inicies la aplicación, este servicio estará disponible en el puerto `8000` por defecto.

Para inicializar la base de datos en DynamoDB Local, debes ejecutar el script `init_db.py`, el cual crea la tabla necesaria en DynamoDB. Para hacerlo, sigue los siguientes pasos:

1. **Ejecutar el script `init_db.py`**

   Asegúrate de que el servicio `vote-db` (DynamoDB Local) esté corriendo antes de ejecutar el script.
   ```bash
   docker compose up vote-db -d  
    ```
   Ejecuta el script `init_db.py` usando Python:

   ```bash
   python init_db.py
   ```
   ```bash
    2025-04-25 22:15:24,423 - __main__ - INFO - Configurando DynamoDB local
    2025-04-25 22:15:24,807 - __main__ - INFO - Creando tabla votes...
    2025-04-25 22:15:24,840 - __main__ - INFO - Esperando a que la tabla se active...
    2025-04-25 22:15:26,845 - __main__ - INFO - Tabla creada correctamente.
    2025-04-25 22:15:26,885 - __main__ - INFO - Inicializando contador para 'cats'
    2025-04-25 22:15:26,900 - __main__ - INFO - Inicializando contador para 'dogs'
    2025-04-25 22:15:26,905 - __main__ - INFO - Base de datos inicializada correctamente.
   ```

   Este script se encargará de crear la tabla `votes` en DynamoDB Local.

### 7. Ejecutar la Aplicación

Una vez que todo esté configurado y hayas inicializado la base de datos, puedes iniciar los servicios con Docker Compose:

```bash
docker compose up
```

Este comando iniciará los servicios `vote` (aplicación Flask) y `vote-db` (DynamoDB Local).

### 8. Acceder a la Aplicación

La aplicación Flask estará accesible en `http://localhost:8080`. Ahora puedes probar la aplicación enviando solicitudes a los siguientes endpoints disponibles:

## Endpoints

### 1. **GET /api/votes**

Este endpoint devuelve todos los votos almacenados en la base de datos de DynamoDB.

- **Método:** GET
- **Descripción:** Obtiene todos los votos almacenados en la tabla DynamoDB.
- **Respuesta exitosa (200):**

  ```json
  [
    {
      "id": "1",
      "option": "Option A",
      "timestamp": "2025-04-25T10:00:00Z"
    },
    {
      "id": "2",
      "option": "Option B",
      "timestamp": "2025-04-25T10:05:00Z"
    }
  ]
  ```

### 2. **POST /api/votes**

Este endpoint permite agregar un voto a la base de datos.

- **Método:** POST
- **Descripción:** Permite a los usuarios votar por una opción.
- **Cuerpo de la solicitud (JSON):**
  
  ```json
  {
    "option": "Option A"
  }
  ```
  
- **Respuesta exitosa (201):**

  ```json
  {
    "id": "3",
    "option": "Option A",
    "timestamp": "2025-04-25T10:10:00Z"
  }
  ```

### 3. **GET /api/votes/{id}**

Este endpoint devuelve un voto específico por su ID.

- **Método:** GET
- **Descripción:** Obtiene los detalles de un voto específico usando su ID.
- **Parámetros:**
  - `id`: El ID del voto a recuperar.
  
- **Respuesta exitosa (200):**

  ```json
  {
    "id": "1",
    "option": "Option A",
    "timestamp": "2025-04-25T10:00:00Z"
  }
  ```

### 4. **DELETE /api/votes/{id}**

Este endpoint elimina un voto específico por su ID.

- **Método:** DELETE
- **Descripción:** Elimina un voto de la base de datos usando su ID.
- **Parámetros:**
  - `id`: El ID del voto a eliminar.
  
- **Respuesta exitosa (200):**

  ```json
  {
    "message": "Vote deleted successfully"
  }
  ```

### 9. Probar la Conexión con DynamoDB

Puedes interactuar con DynamoDB localmente utilizando AWS CLI o tu aplicación. Asegúrate de usar las siguientes credenciales falsas para DynamoDB local:

- `AWS_ACCESS_KEY_ID=FAKE`
- `AWS_SECRET_ACCESS_KEY=FAKE`

Estas están configuradas en el servicio `vote-db` en el archivo `docker-compose.yml`.

### 10. Limpiar el Entorno

Cuando termines de probar, puedes detener los servicios con:

```bash
docker compose down
```

Esto detendrá y eliminará los contenedores. Para eliminar completamente los contenedores y volúmenes, puedes ejecutar:

```bash
docker compose down --volumes
```

## Conclusión

¡Ahora tienes un entorno local completamente funcional para tu aplicación de votación! Puedes interactuar con la aplicación Flask y probar su integración con DynamoDB Local. No olvides ejecutar el script `init_db.py` para inicializar la base de datos antes de empezar a realizar pruebas.
