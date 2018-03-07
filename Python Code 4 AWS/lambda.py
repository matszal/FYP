import boto3
import json

client = boto3.client('iot-data', region_name='eu-west-1')
dynamo = boto3.resource('dynamodb')
table = dynamo.Table('mqtt_table')

# Change topic, qos and payload
def lambda_handler(event, context):
    response = table.scan()
    body = json.dumps(response['Items'])
    response = client.publish(
        topic='mytopic/iot2',
        qos=1,
        payload=body
    )