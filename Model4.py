from aws_session import s3, s3_resource
import json
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

def list_s3_buckets():
    try:
        buckets = s3.list_buckets()['Buckets']

        print("🪣 S3 Bucket 詳細資訊：")
        for bucket in buckets:
            name = bucket['Name']
            created = bucket['CreationDate']
            created_days = (datetime.now(timezone.utc) - created).days

            print(f"\n📦 Bucket: {name}")
            print(f"  📅 建立時間: {created.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  🕒 建立至今: {created_days} 天")

            # 區域資訊
            try:
                region = s3.get_bucket_location(Bucket=name).get('LocationConstraint') or "us-east-1"
                print(f"  🌍 地區: {region}")
            except:
                print("  🌍 地區: 無法取得")

            # 計算檔案數量和總容量
            total_size = 0
            total_objects = 0
            bucket_obj = s3_resource.Bucket(name)
            for obj in bucket_obj.objects.all():
                total_objects += 1
                total_size += obj.size
            print(f"  📦 物件總數: {total_objects}")
            print(f"  📁 總大小: {total_size / 1024 / 1024:.2f} MB")

            # 公開權限
            try:
                block = s3.get_bucket_policy_status(Bucket=name)
                is_public = block.get('PolicyStatus', {}).get('IsPublic', False)
                print(f"  🔒 公開狀態: {'❌ 私有' if not is_public else '⚠️ 公開'}")
            except ClientError:
                print("  🔒 公開狀態: 無法檢查")

            # IAM Policy
            try:
                policy = s3.get_bucket_policy(Bucket=name)
                print("  📜 IAM Policy:")
                print(json.dumps(json.loads(policy['Policy']), indent=4))
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                    print("  📜 IAM Policy: 無")
                else:
                    print("  📜 IAM Policy: 無法取得")

            # Server Side Encryption
            try:
                enc = s3.get_bucket_encryption(Bucket=name)
                rules = enc['ServerSideEncryptionConfiguration']['Rules']
                print("  🛡️ 加密設定:")
                for rule in rules:
                    algo = rule['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
                    print(f"    ➤ 加密方式: {algo}")
            except ClientError:
                print("  🛡️ 加密設定: 未啟用")

            # Logging
            try:
                logging = s3.get_bucket_logging(Bucket=name)
                if logging.get('LoggingEnabled'):
                    target = logging['LoggingEnabled']['TargetBucket']
                    print(f"  📝 Logging 啟用 → 記錄到: {target}")
                else:
                    print("  📝 Logging: 未啟用")
            except Exception:
                print("  📝 Logging: 無法取得")

    except NoCredentialsError:
        print("❌ 無法找到 AWS 憑證。請先執行 aws configure 或確認 .env 設定。")
    except PartialCredentialsError:
        print("❌ AWS 憑證不完整。請確認 .env 檔案內的設定正確。")
    except Exception as e:
        print(f"⚠️ 發生錯誤: {e}")
