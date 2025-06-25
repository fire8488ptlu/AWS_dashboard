# Model3.py
from aws_session import ec2, ec2_client, lambda_client, rds_client, ses_client, s3
import json

def describe_iam_usage():
    print("\n🧭 IAM Role 使用狀況")

    # 🖥️ EC2
    print("\n🖥️ EC2 Instances 使用的 IAM Role：")
    for instance in ec2.instances.all():
        name = "N/A"
        if instance.tags:
            for tag in instance.tags:
                if tag["Key"] == "Name":
                    name = tag["Value"]
        instance_id = instance.id
        profile = instance.iam_instance_profile
        if profile:
            profile_arn = profile['Arn']
            role_name = profile_arn.split('/')[-1]
            print(f"  ▶ EC2: {name} ({instance_id})")
            print(f"    🔗 IAM Role: {role_name}")
        else:
            print(f"  ▶ EC2: {name} ({instance_id})")
            print(f"    ⚠️ 沒有綁定 IAM Role")
    print("-" * 60)

    # 🌀 Lambda
    print("🌀 Lambda Functions 使用的 IAM Role：")
    paginator = lambda_client.get_paginator('list_functions')
    for page in paginator.paginate():
        for fn in page['Functions']:
            fn_name = fn['FunctionName']
            role_arn = fn.get('Role')
            print(f"  ▶ Lambda: {fn_name}")
            print(f"    🔗 IAM Role: {role_arn}")
    print("-" * 60)

    # 🗃️ RDS
    print("🗃️ RDS 使用 IAM 認證：")
    dbs = rds_client.describe_db_instances()['DBInstances']
    for db in dbs:
        dbid = db['DBInstanceIdentifier']
        if db.get('IAMDatabaseAuthenticationEnabled'):
            print(f"  ▶ RDS: {dbid} ✅ IAM Database Authentication 已啟用")
        else:
            print(f"  ▶ RDS: {dbid} ❌ 未啟用 IAM 認證")
    print("-" * 60)

    # ✉️ SES
    print("✉️ SES Identity 使用 IAM 驗證狀況：")
    identities = ses_client.list_identities()['Identities']
    for identity in identities:
        try:
            policy_names = ses_client.list_identity_policies(Identity=identity)['PolicyNames']
            if policy_names:
                print(f"  ▶ SES Identity: {identity} 使用 IAM Policies 發信")
                for pname in policy_names:
                    policy = ses_client.get_identity_policy(Identity=identity, PolicyName=pname)
                    policy_doc = json.loads(policy['Policy'])
                    print(f"    📄 Policy: {pname}")
                    print(json.dumps(policy_doc, indent=4))
            else:
                print(f"  ▶ SES Identity: {identity} 未設定 IAM Policy")
        except Exception as e:
            print(f"  ▶ SES Identity: {identity} ⚠️ 無法取得 Policy - {e}")

    # 🪣 S3
    print("🪣 S3 Buckets 使用 IAM Policy：")
    buckets = s3.list_buckets()['Buckets']
    for bucket in buckets:
        name = bucket['Name']
        try:
            policy_str = s3.get_bucket_policy(Bucket=name)['Policy']
            policy = json.loads(policy_str)
            print(f"  ▶ S3 Bucket: {name}")
            print("    📄 Bucket Policy 使用 IAM：")
            print(json.dumps(policy, indent=4))
        except s3.exceptions.from_code('NoSuchBucketPolicy'):
            print(f"  ▶ S3 Bucket: {name} 沒有 Bucket Policy")
        except Exception as e:
            print(f"  ▶ S3 Bucket: {name} ⚠️ 無法取得 Policy - {e}")
    print("-" * 60)
