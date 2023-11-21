from fastapi import FastAPI, HTTPException, BackgroundTasks
from rediscluster import RedisCluster
import uvicorn
import pika
import uuid

app = FastAPI()
startup_nodes = [{"host": "redisserver.dist-prd", "port": "6379"}]  # Redis 클러스터 노드 정보
redis_client = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)


def redis_set(key: str, value: str):
    redis_client.set(key, value)


def redis_delete(key: str):
    redis_client.delete(key)


@app.post("/create/{key}")
def create_key(background_tasks: BackgroundTasks, key: str, value: str):
    if redis_client.exists(key):
        raise HTTPException(status_code=400, detail="Key already exists")
    background_tasks.add_task(redis_set, key, value)
    return {"key": key, "value": value}


@app.delete("/delete/{key}")
def delete_key(background_tasks: BackgroundTasks, key: str):
    if not redis_client.exists(key):
        raise HTTPException(status_code=404, detail="Key not found")
    background_tasks.add_task(redis_delete, key)
    return {"detail": "Key deleted"}


@app.get("/select/{key}")
def select_key(key: str):
    value = redis_client.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key, "value": value}


rabbitmq_server = 'rabbitmq.common-prd'  # Change as needed
queue_name = 'test_queue'

# Establish RabbitMQ Connection
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_server))
channel = connection.channel()
channel.queue_declare(queue=queue_name)

def insert_message(message):
    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=message)
    print(" [x] Sent %r" % message)

def select_message():
    method_frame, header_frame, body = channel.basic_get(queue=queue_name)
    if method_frame:
        print(" [x] Received %r" % body)
        channel.basic_ack(method_frame.delivery_tag)
        return body
    else:
        print("No message returned")
        return None

@app.post("/insert/")
async def insert(message: str):
    insert_message(message)
    return {"message": "Message sent"}

@app.get("/get/")
async def select():
    message = select_message()
    return {"message": message}

if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", access_log=True, port=8080)
