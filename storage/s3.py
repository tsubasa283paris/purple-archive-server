import os

import boto3
from dotenv import load_dotenv


def upload(src: str, dst: str) -> str:
    load_dotenv()
    
    client = boto3.client("s3")

    region = os.environ["AWS_DEFAULT_REGION"]
    bucket_name = os.environ["AWS_S3_BUCKET_NAME"]

    client.upload_file(
        src,
        bucket_name,
        dst
    )

    return f"https://s3.{region}.amazonaws.com/{bucket_name}/{dst}"
