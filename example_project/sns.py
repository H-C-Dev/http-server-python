import boto3 

client = boto3.client('sns')
import os
sns = boto3.client("sns", region_name="eu-west-2")
from hango.utils import env_loader
env_loader()

SNS_TOPIC = os.environ["SNS_TOPIC"]

def send_email(balance: str):
    response = sns.publish(
    TopicArn=SNS_TOPIC,
    Subject="Starling Balance Alert",
    Message=f"Your account balance is {balance}")
    return response
