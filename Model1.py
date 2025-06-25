from aws_session import (
    ec2, ec2_client, lambda_client, rds_client,
    iam, elb_client,route53
)
from collections import defaultdict

# Utilities

def get_name_from_tags(tags):
    if tags:
        for tag in tags:
            if tag['Key'] == 'Name':
                return tag['Value']
    return 'N/A'

def get_internet_gateway_vpcs():
    igws = ec2_client.describe_internet_gateways()
    vpc_with_igw = set()
    for igw in igws['InternetGateways']:
        for attachment in igw.get('Attachments', []):
            if attachment['State'] == 'available':
                vpc_with_igw.add(attachment['VpcId'])
    return vpc_with_igw

def get_route_table_maps():
    response = ec2_client.describe_route_tables()
    subnet_public_map = {}
    route_table_map = {}

    for rt in response['RouteTables']:
        is_public = False
        for route in rt['Routes']:
            if route.get('GatewayId', '').startswith('igw-'):
                is_public = True

        for assoc in rt.get('Associations', []):
            if assoc.get('SubnetId'):
                subnet_id = assoc['SubnetId']
                subnet_public_map[subnet_id] = is_public
                route_table_map[subnet_id] = rt

    return subnet_public_map, route_table_map

def get_all_lambda_functions():
    lambdas = []
    paginator = lambda_client.get_paginator('list_functions')
    for page in paginator.paginate():
        lambdas.extend(page['Functions'])
    return lambdas

def get_all_rds_instances_grouped_by_vpc():
    rds_instances = rds_client.describe_db_instances()['DBInstances']
    vpc_rds_map = defaultdict(list)
    for db in rds_instances:
        vpc_id = db.get('DBSubnetGroup', {}).get('VpcId')
        if vpc_id:
            vpc_rds_map[vpc_id].append(db)
    return vpc_rds_map

def describe_security_group(sg_id):
    sg = ec2_client.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]
    print(f"        🔐 Security Group: {sg['GroupName']} ({sg['GroupId']})")
    for perm in sg['IpPermissions']:
        protocol = perm.get('IpProtocol', 'all')
        from_port = perm.get('FromPort')
        to_port = perm.get('ToPort')
        port_range = f"{from_port}-{to_port}" if from_port is not None else "all"
        print(f"          Protocol: {protocol} | Port(s): {port_range}")
        for ip_range in perm.get('IpRanges', []):
            print(f"            ➤ Source CIDR: {ip_range.get('CidrIp')}")
        for sg_source in perm.get('UserIdGroupPairs', []):
            print(f"            ➤ Source SG: {sg_source.get('GroupId')}")
        for ipv6_range in perm.get('Ipv6Ranges', []):
            print(f"            ➤ Source IPv6: {ipv6_range.get('CidrIpv6')}")

def get_albs_grouped_by_vpc():
    vpc_albs_map = defaultdict(list)
    albs = elb_client.describe_load_balancers()['LoadBalancers']
    for alb in albs:
        if alb['Type'] == 'application':
            vpc_albs_map[alb['VpcId']].append(alb)
    return vpc_albs_map

def _normalize_dns(name:str) -> str:
    """lower‑case, strip trailing dot and optional dualstack prefix"""
    if not name:
        return ''
    name = name.rstrip('.').lower()
    if name.startswith('dualstack.'):
        name = name[len('dualstack.') :]
    return name



def find_route53_records_for_alb_dns(alb_dns_name):
    """Print Route 53 records (name & type) that alias/CNAME to the given ALB DNS."""
    target = _normalize_dns(alb_dns_name)
    zones = route53.list_hosted_zones()['HostedZones']

    for zone in zones:
        zid = zone['Id'].split('/')[-1]
        records = route53.list_resource_record_sets(HostedZoneId=zid)['ResourceRecordSets']
        for rec in records:
            # Alias A/AAAA
            alias_dns = _normalize_dns(rec.get('AliasTarget', {}).get('DNSName', ''))
            if alias_dns.endswith(target):
                print(f"      🔗 Route53 Alias: {rec['Name']} | Type: {rec['Type']}")
                continue  # found – no need to test CNAME values
            # CNAME values (might be multiple)
            for r in rec.get('ResourceRecords', []):
                if _normalize_dns(r.get('Value')) .endswith(target):
                    print(f"      🔗 Route53 CNAME: {rec['Name']} | Type: {rec['Type']}")
                    break

def describe_albs_in_vpc(vpc_id, albs):
    print(f"\n  🧩 ALBs in this VPC:")
    for alb in albs:
        print(f"    ▶ ALB Name: {alb['LoadBalancerName']}")
        print(f"      ARN: {alb['LoadBalancerArn']}")
        print(f"      Scheme: {alb['Scheme']} (e.g. internet-facing or internal)")
        az_subnets = [az['SubnetId'] for az in alb['AvailabilityZones']]
        print(f"      Subnets:[{', '.join(az_subnets)}]")
        print(f"      DNS Name: {alb['DNSName']}")
        # ⇩ NEW – show Route53 records pointing to this ALB
        find_route53_records_for_alb_dns(alb['DNSName'])
        print(f"      Security Groups: {alb.get('SecurityGroups')}")

        for sg_id in alb.get('SecurityGroups', []):
            describe_security_group(sg_id)

        listeners = elb_client.describe_listeners(LoadBalancerArn=alb['LoadBalancerArn'])['Listeners']
        for listener in listeners:
            print(f"      🔊 Listener:")
            print(f"        Port: {listener['Port']}")
            print(f"        Protocol: {listener['Protocol']}")
            if 'Certificates' in listener:
                for cert in listener['Certificates']:
                    print(f"        SSL Certificate (ACM ARN): {cert.get('CertificateArn')}")
            if 'DefaultActions' in listener:
                for action in listener['DefaultActions']:
                    if action['Type'] == 'forward':
                        tg_arn = action['TargetGroupArn']
                        print(f"        Default Target Group ARN: {tg_arn}")
                        describe_target_group_details(tg_arn)

def describe_vpcs_ec2_lambda_rds():
    vpcs = ec2_client.describe_vpcs()['Vpcs']
    igw_vpcs = get_internet_gateway_vpcs()
    subnet_public_map, route_table_map = get_route_table_maps()
    all_instances = list(ec2.instances.all())
    all_lambdas = get_all_lambda_functions()
    rds_by_vpc = get_all_rds_instances_grouped_by_vpc()

    for vpc in vpcs:
        vpc_id = vpc['VpcId']
        vpc_name = get_name_from_tags(vpc.get('Tags', []))
        print(f"\n🛡️ VPC: {vpc_id} ({vpc_name})")
        print(f"  CIDR: {vpc['CidrBlock']}")
        print(f"  Has Internet Gateway: {'✅ Yes' if vpc_id in igw_vpcs else '❌ No'}")

        subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
        for subnet in subnets:
            subnet_id = subnet['SubnetId']
            subnet_name = get_name_from_tags(subnet.get('Tags', []))
            cidr = subnet['CidrBlock']
            az = subnet['AvailabilityZone']
            is_public = subnet_public_map.get(subnet_id, False)
            rt = route_table_map.get(subnet_id)

            print(f"\n  🌐 Subnet: {subnet_id} ({subnet_name})")
            print(f"    CIDR: {cidr}")
            print(f"    AZ: {az}")
            print(f"    Type: {'Public' if is_public else 'Private'}")
            if rt:
                print("    🔀 Route Table:")
                for route in rt['Routes']:
                    dest = route.get('DestinationCidrBlock') or route.get('DestinationIpv6CidrBlock')
                    target = route.get('GatewayId') or route.get('NatGatewayId') or route.get('TransitGatewayId') or route.get('InstanceId') or 'local'
                    print(f"      - {dest} -> {target}")

        vpc_instances = [i for i in all_instances if any(eni.vpc_id == vpc_id for eni in i.network_interfaces)]
        if vpc_instances:
            print(f"\n  🖥️ EC2 Instances in this VPC:")
            for instance in vpc_instances:
                name = get_name_from_tags(instance.tags)
                print(f"    ▶ Instance Name: {name}")
                print(f"      Instance ID: {instance.id}")
                print(f"      Public IP: {instance.public_ip_address}")
                print(f"      Private IP: {instance.private_ip_address}")
                for interface in instance.network_interfaces:
                    subnet_id = interface.subnet_id
                    is_public = subnet_public_map.get(subnet_id, False)
                    print(f"      Subnet ID: {subnet_id} | Type: {'Public' if is_public else 'Private'}")
                    for sg in interface.groups:
                        describe_security_group(sg['GroupId'])
        else:
            print("  ⚠️ No EC2 instances in this VPC.")

        lambda_in_vpc = [fn for fn in all_lambdas if fn.get('VpcConfig', {}).get('VpcId') == vpc_id]
        if lambda_in_vpc:
            print(f"\n  🌀 Lambda Functions in this VPC:")
            for fn in lambda_in_vpc:
                print(f"    ▶ Lambda Name: {fn['FunctionName']}")
                print(f"      ARN: {fn['FunctionArn']}")
                print(f"      Runtime: {fn.get('Runtime')}")
                print(f"      Timeout: {fn.get('Timeout')} sec")
                subnet_ids = fn['VpcConfig'].get('SubnetIds', [])
                sg_ids = fn['VpcConfig'].get('SecurityGroupIds', [])
                print(f"      Subnet IDs: {subnet_ids}")
                print(f"      Security Group IDs: {sg_ids}")
                for sg_id in sg_ids:
                    describe_security_group(sg_id)
        else:
            print("  ⚠️ No Lambda functions in this VPC.")

        if vpc_id in rds_by_vpc:
            print(f"\n  🗃️ RDS Instances in this VPC:")
            for db in rds_by_vpc[vpc_id]:
                print(f"    ▶ DB Identifier: {db['DBInstanceIdentifier']}")
                print(f"      Engine: {db['Engine']}")
                print(f"      DB Class: {db['DBInstanceClass']}")
                print(f"      Subnet Group: {db['DBSubnetGroup']['DBSubnetGroupName']}")
                print(f"      Subnets: {[s['SubnetIdentifier'] for s in db['DBSubnetGroup']['Subnets']]}")
                print(f"      Public Access: {'✅ Yes' if db['PubliclyAccessible'] else '❌ No'}")
                for sg in db.get('VpcSecurityGroups', []):
                    describe_security_group(sg['VpcSecurityGroupId'])
        else:
            print("  ⚠️ No RDS instances in this VPC.")

        albs_by_vpc = get_albs_grouped_by_vpc()
        vpc_albs = albs_by_vpc.get(vpc_id, [])
        if vpc_albs:
            describe_albs_in_vpc(vpc_id, vpc_albs)
        else:
            print("  ⚠️ No ALBs in this VPC.")

        print("-" * 80)

    lambda_without_vpc = [fn for fn in all_lambdas if not fn.get('VpcConfig', {}).get('VpcId')]
    if lambda_without_vpc:
        print("\n📦 Lambda Functions NOT Bound to Any VPC:")
        for fn in lambda_without_vpc:
            print(f"  ▶ Lambda Name: {fn['FunctionName']}")
            print(f"    ARN: {fn['FunctionArn']}")
            print(f"    Runtime: {fn.get('Runtime')}")
            print(f"    Timeout: {fn.get('Timeout')} sec")
    else:
        print("\n✅ All Lambda functions are assigned to a VPC.")


import boto3

def describe_target_group_details(tg_arn):
    tg = elb_client.describe_target_groups(TargetGroupArns=[tg_arn])['TargetGroups'][0]
    print(f"        ➤ Target Group Name: {tg['TargetGroupName']}")
    print(f"          Target Type: {tg['TargetType']}")
    print(f"          Protocol: {tg['Protocol']} | Port: {tg['Port']}")
    print(f"          VPC ID: {tg['VpcId']}")

    targets = elb_client.describe_target_health(TargetGroupArn=tg_arn)['TargetHealthDescriptions']
    if not targets:
        print(f"          No targets registered.")
    else:
        print(f"          Registered Targets:")
        for target in targets:
            target_id = target['Target']['Id']
            port = target['Target']['Port']
            health = target['TargetHealth']['State']

            # Describe the EC2 instance to get its name and IP
            try:
                instance = ec2.Instance(target_id)
                instance_name = get_name_from_tags(instance.tags)
                private_ip = instance.private_ip_address
                print(f"            ▶ EC2 Instance: {instance_name} ({target_id})")
                print(f"              ➤ Private IP: {private_ip}")
                print(f"              ➤ Port: {port} | Health: {health}")
            except Exception as e:
                print(f"            ▶ Target ID: {target_id} | Port: {port} | Health: {health} (⚠️ Not EC2?)")

