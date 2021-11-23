import boto3
import os

REGION = os.environ['REGION']

# function => to get aws instance id
def instanceIds():
    ids = []
    ec2 = boto3.session.Session(region_name=REGION).resource('ec2')
    for instance in ec2.instances.all():
        ids.append(instance.id)
    return ids

# function => to delete the aws instance
def deleteInstance(ids):
    if ids != []:
        ec2 = boto3.session.Session(region_name=REGION).resource('ec2')
        ec2.instances.filter(InstanceIds=ids).terminate()
    else:
        print("instance not found.")

def lambda_handler(event, context):
    deleteInstance(instanceIds())
