from Model1 import describe_vpcs_ec2_lambda_rds
from Model2 import describe_iam_resources
from Model3 import describe_iam_usage
from Model4 import list_s3_buckets
from Model5 import describe_route53_acm_cloudfront

import traceback
import time

def main_menu():
    while True:
        print("\n📦 AWS 資源總覽工具")
        print("1️⃣ 查看 VPC/EC2/Lambda/RDS/ALB 資訊")
        print("2️⃣ 查看 IAM 使用者/角色/群組")
        print("3️⃣ 查看 IAM 使用狀況")
        print("4️⃣ 查看 S3 Bucket 詳細資訊")
        print("5️⃣ 查看 Route53/ACM/CloudFront 資訊")
        print("0️⃣ 離開")

        choice = input("請輸入選項號碼：")
        try:
            if choice == '1':
                describe_vpcs_ec2_lambda_rds()
            elif choice == '2':
                describe_iam_resources()
            elif choice == '3':
                describe_iam_usage()
            elif choice == '4':
                list_s3_buckets()
            elif choice == '5':
                describe_route53_acm_cloudfront()
            elif choice == '0':
                print("👋 離開系統，再見！")
                break
            else:
                print("❌ 無效的選項，請重新輸入。")
        except Exception as e:
            print("\n⚠️ 程式發生錯誤！以下是詳細錯誤訊息：\n")
            traceback.print_exc()

        input("\n🔚 按下 Enter 繼續...")

if __name__ == "__main__":
    main_menu()
