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






def getVpcIds():
    vpcIds = []
    client = boto3.client('ec2',region_name=REGION)
    response = client.describe_vpcs()
    vpcIds.append(response['Vpcs'][0]['VpcId'])
    return vpcIds



def vpc_cleanup(vpcid):
    """Remove VPC from AWS
    Set your region/access-key/secret-key from env variables or boto config.
    :param vpcid: id of vpc to delete
    """
    if not vpcid:
        return
    print('Removing VPC ({}) from AWS'.format(vpcid))
    ec2 = boto3.session.Session(region_name=REGION).resource('ec2')
    ec2client = ec2.meta.client
    vpc = ec2.Vpc(vpcid)
    # detach default dhcp_options if associated with the vpc
    dhcp_options_default = ec2.DhcpOptions('default')
    if dhcp_options_default:
        dhcp_options_default.associate_with_vpc(
            VpcId=vpc.id
        )
    # detach and delete all gateways associated with the vpc
    for gw in vpc.internet_gateways.all():
        vpc.detach_internet_gateway(InternetGatewayId=gw.id)
        gw.delete()
    # delete all route table associations
    for rt in vpc.route_tables.all():
        for rta in rt.associations:
            if not rta.main:
                rta.delete()
    # delete any instances
    for subnet in vpc.subnets.all():
        for instance in subnet.instances.all():
            instance.terminate()
    # delete our endpoints
    for ep in ec2client.describe_vpc_endpoints(
            Filters=[{
                'Name': 'vpc-id',
                'Values': [vpcid]
            }])['VpcEndpoints']:
        ec2client.delete_vpc_endpoints(VpcEndpointIds=[ep['VpcEndpointId']])
    # delete our security groups
    for sg in vpc.security_groups.all():
        if sg.group_name != 'default':
            sg.delete()
    # delete any vpc peering connections
    for vpcpeer in ec2client.describe_vpc_peering_connections(
            Filters=[{
                'Name': 'requester-vpc-info.vpc-id',
                'Values': [vpcid]
            }])['VpcPeeringConnections']:
        ec2.VpcPeeringConnection(vpcpeer['VpcPeeringConnectionId']).delete()
    # delete non-default network acls
    for netacl in vpc.network_acls.all():
        if not netacl.is_default:
            netacl.delete()
    # delete network interfaces
    for subnet in vpc.subnets.all():
        for interface in subnet.network_interfaces.all():
            interface.delete()
        subnet.delete()
    # finally, delete the vpc
    ec2client.delete_vpc(VpcId=vpcid)



def vpc_cleanups():
    ids = getVpcIds()
    if ids != []:
        for i in getVpcIds():
            vpc_cleanup(i)
    else:
        print("vpc not found.")




def lambda_handler(event, context):
    deleteInstance(instanceIds())
    deleteDbInstance(getDbInstanceIds())
    deleteBuckets(getS3Buckets())
    vpc_cleanups()
