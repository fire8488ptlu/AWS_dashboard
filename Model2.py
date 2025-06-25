# Model2.py
from aws_session import iam
import json

def get_policy_detail(policy_arn):
    try:
        policy = iam.get_policy(PolicyArn=policy_arn)['Policy']
        version_id = policy['DefaultVersionId']
        policy_version = iam.get_policy_version(
            PolicyArn=policy_arn,
            VersionId=version_id
        )['PolicyVersion']

        document = policy_version['Document']
        statements = document.get("Statement", [])
        if not isinstance(statements, list):
            statements = [statements]

        # 🔍 判斷風險等級
        risk_level = "🟢"
        for stmt in statements:
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            if "*" in actions:
                risk_level = "🔴"
                break
            elif any(a.startswith(("iam:*", "s3:*", "ec2:*")) for a in actions):
                risk_level = "🕀"

        # 🔨 輸出 policy document
        print(f"{risk_level} Policy Statement:")
        print(json.dumps(document, indent=4))

    except Exception as e:
        print(f"        ⚠️ 無法讀取 Policy 詳細內容：{e}")

def describe_iam_resources():
    print("\n🔐 IAM 資源總覽")

    # 👤 IAM Users
    print("\n👤 IAM Users:")
    users = iam.list_users()['Users']
    for user in users:
        user_name = user['UserName']
        print(f"\n  ▶ User: {user_name}")

        attached = iam.list_attached_user_policies(UserName=user_name)['AttachedPolicies']
        if attached:
            print(f"    🔗 Attached Policies:")
            for policy in attached:
                print(f"      - {policy['PolicyName']}")
                get_policy_detail(policy['PolicyArn'])
        else:
            print("    ❌ No direct policies.")

        groups = iam.list_groups_for_user(UserName=user_name)['Groups']
        if groups:
            print(f"    👥 Member of Groups:")
            for g in groups:
                print(f"      - {g['GroupName']}")
        else:
            print("    ❌ Not in any group.")

    # 👥 IAM Groups
    print("\n👥 IAM Groups:")
    groups = iam.list_groups()['Groups']
    for group in groups:
        group_name = group['GroupName']
        print(f"\n  ▶ Group: {group_name}")
        users = iam.get_group(GroupName=group_name)['Users']
        print(f"    👤 Users: {[u['UserName'] for u in users]}")
        policies = iam.list_attached_group_policies(GroupName=group_name)['AttachedPolicies']
        if policies:
            print(f"    🔗 Attached Policies:")
            for p in policies:
                print(f"      - {p['PolicyName']}")
                get_policy_detail(p['PolicyArn'])
        else:
            print("    ❌ No attached policies.")

    # 🧹 Custom IAM Policies
    print("\n📄 Custom IAM Policies:")
    policies = iam.list_policies(Scope='Local')['Policies']
    for policy in policies:
        print(f"\n  ▶ Policy Name: {policy['PolicyName']} | ARN: {policy['Arn']}")
        get_policy_detail(policy['Arn'])
