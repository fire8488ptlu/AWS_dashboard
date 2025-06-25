# aws_session.py
import os
import boto3
from dotenv import load_dotenv
from pathlib import Path
import sys
import traceback

# ✅ 載入 .env（支援 exe）
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    print("❌ 找不到 .env 檔案，請確認它與程式在同一資料夾")
    input("🔚 按下 Enter 結束")
    sys.exit(1)

load_dotenv(dotenv_path=env_path)

# ✅ 讀取憑證環境變數
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

# ✅ 建立 AWS session（完整憑證）
try:
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

    # ✅ 建立各 client/resource
    ec2 = session.resource('ec2')
    ec2_client = session.client('ec2')
    lambda_client = session.client('lambda')
    rds_client = session.client('rds')
    ses_client = session.client('ses')
    s3 = session.client('s3')
    s3_resource = session.resource('s3')
    iam = session.client('iam')
    elb_client = session.client('elbv2')
    cloudfront = session.client('cloudfront')
    acm = session.client('acm')
    route53 = session.client('route53')

except Exception as e:
    print("❌ 建立 AWS Session 或初始化 client 時發生錯誤：")
    traceback.print_exc()
    input("🔚 按下 Enter 結束")
    sys.exit(1)
