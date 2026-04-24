"""S3 client for storing transcripts + notes (never audio)."""

from __future__ import annotations

import json
from typing import Any

import boto3
from botocore.config import Config as BotoConfig

from ..core.config import Settings


def s3_client(settings: Settings) -> Any:
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url or None,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        config=BotoConfig(signature_version="s3v4"),
    )


def upload_transcript(settings: Settings, meeting_id: str, payload: dict) -> str:
    client = s3_client(settings)
    key = f"transcripts/{meeting_id}.json"
    client.put_object(
        Bucket=settings.s3_bucket_transcripts,
        Key=key,
        Body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
    return key
