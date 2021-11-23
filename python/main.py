import boto3
import os

REGION = os.environ['REGION']

def instanceIds():
    ids = []
    ec2 = boto3.resource('ec2')
    for instance in ec2.instances.all():
        ids.append(instance.id)
    return ids

def deleteInstance(ids):
    if ids != []:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=ids).terminate()
    else:
        print("instance not found.")


def lambda_handler(event, context):
    deleteInstance(instanceIds())
