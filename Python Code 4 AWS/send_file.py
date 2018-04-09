import boto3
from botocore.client import Config

ACCESS_KEY_ID 		= open("/home/pi/Desktop/pythonForAWS/certs/key.txt", "r").read()
ACCESS_SECRET_KEY 	= open("/home/pi/Desktop/pythonForAWS/certs/skey.txt", "r").read()
BUCKET_NAME 		= open("/home/pi/Desktop/pythonForAWS/certs/bucket.txt", "r").read()





def store_to_bucket(path, date):

        data = open(path, 'rb')
        ext = '.jpg'	

	s3 = boto3.resource(
		's3',
		aws_access_key_id=ACCESS_KEY_ID,
		aws_secret_access_key=ACCESS_SECRET_KEY,
		config=Config(signature_version='s3v4')
	)

	s3.Bucket(BUCKET_NAME).put_object(Key=date+ext, Body=data)

        print ("Done")
