import boto3
import os

REGION = os.environ['REGION']

# EC2
def instanceIds():
    ids = []
    ec2 = boto3.session.Session(region_name=REGION).resource('ec2')
    for instance in ec2.instances.all():
        ids.append(instance.id)
    return ids

def deleteInstance(ids):
    if ids != []:
        ec2 = boto3.session.Session(region_name=REGION).resource('ec2')
        ec2.instances.filter(InstanceIds=ids).terminate()
    else:
        print("instance not found.")

# RDS
def getDbInstanceIds():
    dbIds = []
    client = boto3.session.Session(region_name=REGION).client('rds')
    response = client.describe_db_instances()
    for i in response['DBInstances']:
        db_instance_name = i['DBInstanceIdentifier']
        dbIds.append(db_instance_name)
    return dbIds

def deleteDbInstance(dbInstanceIds):
    if dbInstanceIds != []:
        for i in dbInstanceIds:
            client = boto3.session.Session(region_name=REGION).client('rds')
            client.delete_db_instance(
            DBInstanceIdentifier=i,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True
        )
    else:
        print("Rds instance not found")

# S3

def getS3Buckets():
    getS3Buckets = []
    client = boto3.session.Session(region_name=REGION).resource('s3')
    for bucket in client.buckets.all():
        getS3Buckets.append(bucket.name)
        print(bucket.name)
    return getS3Buckets

def deleteBuckets(getS3Buckets):
    if getS3Buckets != []:
        for buck in getS3Buckets:
            s3_client = boto3.session.Session(region_name=REGION).client('s3')
            bucket = buck
            # s3_client = boto3.client('s3')
            object_response_paginator = s3_client.get_paginator('list_object_versions')
            
            delete_marker_list = []
            version_list = []
            
            for object_response_itr in object_response_paginator.paginate(Bucket=bucket):
                if 'DeleteMarkers' in object_response_itr:
                    for delete_marker in object_response_itr['DeleteMarkers']:
                        delete_marker_list.append({'Key': delete_marker['Key'], 'VersionId': delete_marker['VersionId']})
            
                if 'Versions' in object_response_itr:
                    for version in object_response_itr['Versions']:
                        version_list.append({'Key': version['Key'], 'VersionId': version['VersionId']})
            
            for i in range(0, len(delete_marker_list), 1000):
                response = s3_client.delete_objects(
                    Bucket=bucket,
                    Delete={
                        'Objects': delete_marker_list[i:i+1000],
                        'Quiet': True
                    }
                )
                print(response)
            
            for i in range(0, len(version_list), 1000):
                response = s3_client.delete_objects(
                    Bucket=bucket,
                    Delete={
                        'Objects': version_list[i:i+1000],
                        'Quiet': True
                    }
                )
                print(response)

            s3_client.delete_bucket(Bucket=buck)
    else:
        print('S3 buckets not found')

def lambda_handler(event, context):
    deleteInstance(instanceIds())
    deleteDbInstance(getDbInstanceIds())
    deleteBuckets(getS3Buckets())
