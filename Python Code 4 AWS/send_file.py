import boto3
from botocore.client import Config

ACCESS_KEY_ID 			= open("/home/pi/Desktop/pythonForAWS/certs/key.txt", "r")
ACCESS_SECRET_KEY 		= open("/home/pi/Desktop/pythonForAWS/certs/skey.txt", "r")
BUCKET_NAME 			= open("/home/pi/Desktop/pythonForAWS/certs/bucket.txt", "r")

data = open('sample1.png', 'rb')

s3 = boto3.resource(
	's3',
	aws_access_key_id=ACCESS_KEY_ID.read(),
    aws_secret_access_key=ACCESS_SECRET_KEY.read(),
    config=Config(signature_version='s3v4')
)
s3.Bucket(BUCKET_NAME.read()).put_object(Key='sample2.png', Body=data)

print ("Done")
