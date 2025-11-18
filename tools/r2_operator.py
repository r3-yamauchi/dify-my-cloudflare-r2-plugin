"""
場所: tools/r2_operator.py
内容: R2 オブジェクトに対する読み書きおよびプリサイン URL 生成を行うユーティリティツール。
目的: Dify Workflow から R2 上のテキストファイルを簡単に操作できるようにする。
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any, Optional, TYPE_CHECKING
from urllib.parse import urlparse

from botocore.exceptions import ClientError

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

try:
    from cloudflare_r2_tools.provider.utils import initialize_r2_client, handle_r2_client_error
except ModuleNotFoundError:  # pragma: no cover
    from provider.utils import initialize_r2_client, handle_r2_client_error

if TYPE_CHECKING:
    # 型チェック時のみインポート
    try:
        from mypy_boto3_s3 import S3Client
    except ImportError:
        from botocore.client import BaseClient
        S3Client = BaseClient
else:
    S3Client = Any


class R2Operator(Tool):
    r2_client: Optional[S3Client] = None

    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage]:
        """R2 の read/write 操作を実行し、必要に応じてプリサイン URL を返す."""
        try:
            self.r2_client = initialize_r2_client(self, tool_parameters)
        except Exception as exc:
            yield self.create_text_message(f"Failed to initialize R2 client: {exc}")
            return

        # R2 URI を解析
        r2_uri = tool_parameters.get("r2_uri")
        if not r2_uri:
            yield self.create_text_message("r2_uri parameter is required")
            return

        parsed_uri = urlparse(r2_uri)
        # r2:// または s3:// の両方を受け入れる（互換性のため）
        if parsed_uri.scheme not in ("r2", "s3"):
            yield self.create_text_message("Invalid R2 URI format. Must start with 'r2://' or 's3://'")
            return

        bucket = parsed_uri.netloc
        key = parsed_uri.path.lstrip("/")  # 先頭のスラッシュを除去

        if not self.r2_client:
            yield self.create_text_message("R2 client is not initialized")
            return

        operation_type = tool_parameters.get("operation_type", "read")
        generate_presign_url = tool_parameters.get("generate_presign_url", False)
        presign_expiry = int(tool_parameters.get("presign_expiry", 3600))  # default 1 hour

        try:
            if operation_type == "write":
                text_content = tool_parameters.get("text_content")
                if not text_content:
                    yield self.create_text_message("text_content parameter is required for write operation")
                    return

                # テキストを R2 に書き込む
                self.r2_client.put_object(Bucket=bucket, Key=key, Body=text_content.encode("utf-8"))
                r2_uri = f"r2://{bucket}/{key}"
                result = r2_uri

                # 必要なら書き込んだオブジェクトのプリサイン URL を返す
                if generate_presign_url:
                    presigned_url = self.r2_client.generate_presigned_url(
                        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=presign_expiry
                    )
                    result = presigned_url
                    
                    result_payload = {
                        "operation": "write",
                        "bucket": bucket,
                        "key": key,
                        "r2_uri": r2_uri,
                        "presigned_url": presigned_url,
                        "presign_expiry": presign_expiry,
                    }
                else:
                    result_payload = {
                        "operation": "write",
                        "bucket": bucket,
                        "key": key,
                        "r2_uri": r2_uri,
                    }

            else:  # read operation
                # R2 から読み取る
                if generate_presign_url:
                    # 読み込み用のプリサイン URL を返す
                    presigned_url = self.r2_client.generate_presigned_url(
                        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=presign_expiry
                    )
                    result = presigned_url
                    
                    result_payload = {
                        "operation": "read",
                        "bucket": bucket,
                        "key": key,
                        "r2_uri": f"r2://{bucket}/{key}",
                        "presigned_url": presigned_url,
                        "presign_expiry": presign_expiry,
                    }
                else: 
                    # テキストとして直接取得
                    response = self.r2_client.get_object(Bucket=bucket, Key=key)
                    text_content = response["Body"].read().decode("utf-8")
                    result = text_content
                    
                    result_payload = {
                        "operation": "read",
                        "bucket": bucket,
                        "key": key,
                        "r2_uri": f"r2://{bucket}/{key}",
                        "text_content": text_content,
                        "content_length": len(text_content.encode("utf-8")),
                    }

            yield self.create_json_message(result_payload)
            yield self.create_text_message(text=result)

        except ClientError as exc:
            operation = "write" if operation_type == "write" else "read"
            error_message = handle_r2_client_error(exc, operation, bucket=bucket, key=key)
            yield self.create_text_message(error_message)
        except Exception as exc:
            operation = "write" if operation_type == "write" else "read"
            error_message = handle_r2_client_error(exc, operation, bucket=bucket, key=key)
            yield self.create_text_message(error_message)

