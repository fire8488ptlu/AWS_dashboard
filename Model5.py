# Model5.py
from aws_session import route53, cloudfront, acm
from collections import defaultdict

def describe_route53_acm_cloudfront():
    print("\n📘 Route53 Hosted Zones & Records:")
    hosted_zones = route53.list_hosted_zones()['HostedZones']

    for zone in sorted(hosted_zones, key=lambda z: z['Name']):
        zone_id = zone['Id'].split('/')[-1]
        zone_name = zone['Name']
        print(f"\n🔹 Hosted Zone: {zone_name} (ID: {zone_id})")

        records_by_type = defaultdict(list)
        records = route53.list_resource_record_sets(HostedZoneId=zone_id)['ResourceRecordSets']
        for record in records:
            records_by_type[record['Type']].append(record)

        for record_type in sorted(records_by_type.keys()):
            print(f"  📄 {record_type} Records:")
            for record in records_by_type[record_type]:
                name = record['Name']
                value = (
                    record.get('AliasTarget', {}).get('DNSName') or
                    (record['ResourceRecords'][0]['Value'] if 'ResourceRecords' in record else 'N/A')
                )
                print(f"    ▶ {name} ➡ {value}")

    print("\n🚀 CloudFront Distributions:")
    dists = cloudfront.list_distributions().get('DistributionList', {}).get('Items', [])
    for dist in dists:
        dist_id = dist['Id']
        domain_name = dist['DomainName']
        aliases = dist.get('Aliases', {}).get('Items', [])
        cert_arn = dist.get('ViewerCertificate', {}).get('ACMCertificateArn', '無')
        origin_domain = dist['Origins']['Items'][0]['DomainName']

        print(f"\n🔹 Distribution ID: {dist_id}")
        print(f"  🌐 CloudFront Domain: {domain_name}")
        print(f"  🎯 Origin: {origin_domain}")
        print(f"  🧾 Aliases (CNAMEs): {aliases if aliases else '無'}")
        print(f"  🔐 ACM Certificate ARN: {cert_arn}")

    print("\n📜 ACM Certificates:")
    certs = acm.list_certificates(CertificateStatuses=['ISSUED'])['CertificateSummaryList']
    for cert in certs:
        cert_arn = cert['CertificateArn']
        cert_detail = acm.describe_certificate(CertificateArn=cert_arn)['Certificate']
        domains = cert_detail['SubjectAlternativeNames']
        in_use = cert_detail.get('InUseBy', [])
        print(f"\n🔹 Certificate ARN: {cert_arn}")
        print(f"  🌐 Domains: {domains}")
        print(f"  🛠️ In Use By: {in_use if in_use else '未綁定服務'}")


'''
import os
import json
import boto3
from dotenv import load_dotenv
from collections import defaultdict
from pathlib import Path
import sys
import traceback

# 使用絕對路徑載入 .env（適用打包 .exe）
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    print("❌ 找不到 .env 檔案，請確認它與程式在同一資料夾")
    input("🔚 按下 Enter 結束")
    sys.exit(1)

load_dotenv(dotenv_path=env_path)

# 讀取 AWS 環境變數
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION")

missing = []
if not AWS_ACCESS_KEY: missing.append("AWS_ACCESS_KEY")
if not AWS_SECRET_KEY: missing.append("AWS_SECRET_KEY")
if not AWS_REGION: missing.append("AWS_REGION")

if missing:
    print(f"❌ 缺少以下 .env 設定：{', '.join(missing)}")
    input("🔚 按下 Enter 結束")
    sys.exit(1)

# 建立 AWS Session（含完整錯誤處理）
try:
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

    # 初始化 service clients
    route53 = session.client('route53')
    cloudfront = session.client('cloudfront')
    acm = session.client('acm')

except Exception as e:
    print("❌ 建立 AWS Session 或初始化服務時發生錯誤：")
    traceback.print_exc()
    input("🔚 按下 Enter 結束")
    sys.exit(1)

def describe_route53_acm_cloudfront():
    route53 = boto3.client('route53')
    cloudfront = boto3.client('cloudfront')
    acm = boto3.client('acm')

    # 🔹 Route53 Hosted Zones & Records
    print("\n📘 Route53 Hosted Zones & Records:")
    hosted_zones = route53.list_hosted_zones()['HostedZones']

    for zone in sorted(hosted_zones, key=lambda z: z['Name']):
        zone_id = zone['Id'].split('/')[-1]
        zone_name = zone['Name']
        print(f"\n🔹 Hosted Zone: {zone_name} (ID: {zone_id})")

        # 分類記錄：依照 Type（A, AAAA, CNAME, etc）整理
        records_by_type = defaultdict(list)
        records = route53.list_resource_record_sets(HostedZoneId=zone_id)['ResourceRecordSets']
        for record in records:
            records_by_type[record['Type']].append(record)

        for record_type in sorted(records_by_type.keys()):
            print(f"  📄 {record_type} Records:")
            for record in records_by_type[record_type]:
                name = record['Name']
                value = (
                    record.get('AliasTarget', {}).get('DNSName') or
                    (record['ResourceRecords'][0]['Value'] if 'ResourceRecords' in record else 'N/A')
                )
                print(f"    ▶ {name} ➡ {value}")

    # 🔸 CloudFront Distributions
    print("\n🚀 CloudFront Distributions:")
    dists = cloudfront.list_distributions().get('DistributionList', {}).get('Items', [])
    for dist in dists:
        dist_id = dist['Id']
        domain_name = dist['DomainName']
        aliases = dist.get('Aliases', {}).get('Items', [])
        cert_arn = dist.get('ViewerCertificate', {}).get('ACMCertificateArn', '無')
        origin_domain = dist['Origins']['Items'][0]['DomainName']

        print(f"\n🔹 Distribution ID: {dist_id}")
        print(f"  🌐 CloudFront Domain: {domain_name}")
        print(f"  🎯 Origin: {origin_domain}")
        print(f"  🧾 Aliases (CNAMEs): {aliases if aliases else '無'}")
        print(f"  🔐 ACM Certificate ARN: {cert_arn}")

    # 🔐 ACM Certificates
    print("\n📜 ACM Certificates:")
    certs = acm.list_certificates(CertificateStatuses=['ISSUED'])['CertificateSummaryList']
    for cert in certs:
        cert_arn = cert['CertificateArn']
        cert_detail = acm.describe_certificate(CertificateArn=cert_arn)['Certificate']
        domains = cert_detail['SubjectAlternativeNames']
        in_use = cert_detail.get('InUseBy', [])
        print(f"\n🔹 Certificate ARN: {cert_arn}")
        print(f"  🌐 Domains: {domains}")
        print(f"  🛠️ In Use By: {in_use if in_use else '未綁定服務'}")

'''