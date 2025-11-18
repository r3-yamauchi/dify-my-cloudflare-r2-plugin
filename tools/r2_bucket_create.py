"""
場所: tools/r2_bucket_create.py
内容: R2 アカウントに新しいバケットを作成するツール。
目的: ワークフローから新しいバケットを作成できるようにする。
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any, Optional, TYPE_CHECKING

from botocore.exceptions import ClientError

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

try:
    from cloudflare_r2_tools.provider.utils import (
        initialize_r2_client,
        handle_r2_client_error,
        resolve_r2_credentials,
    )
except ModuleNotFoundError:  # pragma: no cover
    from provider.utils import (
        initialize_r2_client,
        handle_r2_client_error,
        resolve_r2_credentials,
    )

if TYPE_CHECKING:
    # 型チェック時のみインポート
    try:
        from mypy_boto3_s3 import S3Client
    except ImportError:
        from botocore.client import BaseClient
        S3Client = BaseClient
else:
    S3Client = Any


def _validate_bucket_name(bucket_name: str) -> tuple[bool, str | None]:
    """
    バケット名の形式を検証する。
    
    Args:
        bucket_name: 検証するバケット名
        
    Returns:
        (is_valid, error_message) のタプル
    """
    if not bucket_name:
        return False, "Bucket name cannot be empty"
    
    if len(bucket_name) < 3:
        return False, "Bucket name must be at least 3 characters long"
    
    if len(bucket_name) > 63:
        return False, "Bucket name must be no more than 63 characters long"
    
    # バケット名は小文字のみ許可
    if bucket_name != bucket_name.lower():
        return False, "Bucket name must contain only lowercase letters"
    
    # バケット名は小文字、数字、ハイフン、ドットのみ許可
    if not bucket_name.replace("-", "").replace(".", "").isalnum():
        return False, "Bucket name can only contain lowercase letters, numbers, hyphens, and dots"
    
    # 連続するドットやハイフンは許可しない
    if ".." in bucket_name or "--" in bucket_name:
        return False, "Bucket name cannot contain consecutive dots or hyphens"
    
    # ドットとハイフンを隣接させない
    if "-." in bucket_name or ".-" in bucket_name:
        return False, "Bucket name cannot contain adjacent dots and hyphens"
    
    # 先頭と末尾は文字または数字でなければならない
    if not bucket_name[0].isalnum() or not bucket_name[-1].isalnum():
        return False, "Bucket name must start and end with a letter or number"
    
    # IPアドレス形式は許可しない
    parts = bucket_name.split(".")
    if len(parts) == 4 and all(part.isdigit() for part in parts if part):
        return False, "Bucket name cannot be formatted as an IP address"
    
    return True, None


class R2BucketCreate(Tool):
    r2_client: Optional[S3Client] = None

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """R2 アカウントに新しいバケットを作成し、結果を返す。"""
        try:
            self.r2_client = initialize_r2_client(self, tool_parameters)
        except Exception as exc:
            yield self.create_text_message(f"Failed to initialize R2 client: {exc}")
            return

        if not self.r2_client:
            yield self.create_text_message("R2 client is not initialized")
            return

        bucket_name = tool_parameters.get("bucket_name")
        if not bucket_name:
            yield self.create_text_message("bucket_name parameter is required")
            return

        # バケット名の検証
        is_valid, error_message = _validate_bucket_name(bucket_name)
        if not is_valid:
            yield self.create_text_message(f"Invalid bucket name: {error_message}")
            return

        # リージョン名を取得（デフォルトは'auto'）
        credentials = resolve_r2_credentials(self, tool_parameters)
        region_name = credentials.get('region_name', 'auto')

        try:
            # R2では、create_bucketはLocationConstraintを必要としない
            # ただし、リージョン名を指定する場合はLocationConstraintを使用
            create_kwargs: dict[str, Any] = {
                "Bucket": bucket_name,
            }
            
            # R2では通常LocationConstraintは不要だが、明示的に指定することも可能
            # Cloudflare R2の場合は、LocationConstraintを指定しないか、または'auto'を使用
            
            self.r2_client.create_bucket(**create_kwargs)
            
            result_payload = {
                "bucket_name": bucket_name,
                "region": region_name,
                "r2_uri": f"r2://{bucket_name}/",
                "created": True,
            }
            
            yield self.create_json_message(result_payload)
            yield self.create_text_message(f"Successfully created bucket: {bucket_name}")
            
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code == "BucketAlreadyExists":
                yield self.create_text_message(f"Bucket '{bucket_name}' already exists")
            elif error_code == "BucketAlreadyOwnedByYou":
                yield self.create_text_message(f"Bucket '{bucket_name}' is already owned by you")
            else:
                error_message = handle_r2_client_error(exc, "create bucket", bucket=bucket_name)
                yield self.create_text_message(error_message)
        except Exception as exc:
            error_message = handle_r2_client_error(exc, "create bucket", bucket=bucket_name)
            yield self.create_text_message(error_message)

