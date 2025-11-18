"""
場所: tools/r2_object_delete.py
内容: R2 バケット内のオブジェクトを削除するツール。
目的: ワークフローから不要なオブジェクトを削除できるようにする。
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


class R2ObjectDelete(Tool):
    r2_client: Optional[S3Client] = None

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """R2 バケット内のオブジェクトを削除し、結果を返す。"""
        try:
            self.r2_client = initialize_r2_client(self, tool_parameters)
        except Exception as exc:
            yield self.create_text_message(f"Failed to initialize R2 client: {exc}")
            return

        if not self.r2_client:
            yield self.create_text_message("R2 client is not initialized")
            return

        r2_uri = tool_parameters.get("r2_uri")
        if not r2_uri:
            yield self.create_text_message("r2_uri parameter is required")
            return

        parsed_uri = urlparse(r2_uri)
        # r2:// または s3:// の両方を受け入れる（互換性のため）
        if parsed_uri.scheme not in ("r2", "s3") or not parsed_uri.netloc or not parsed_uri.path:
            yield self.create_text_message("Invalid R2 URI format. Use r2://bucket/key or s3://bucket/key")
            return

        bucket = parsed_uri.netloc
        key = parsed_uri.path.lstrip("/")

        try:
            self.r2_client.delete_object(Bucket=bucket, Key=key)
            
            result_payload = {
                "bucket": bucket,
                "key": key,
                "r2_uri": r2_uri,
                "deleted": True,
            }
            
            yield self.create_json_message(result_payload)
            yield self.create_text_message(f"Successfully deleted object: {r2_uri}")
            
        except ClientError as exc:
            error_message = handle_r2_client_error(exc, "delete", bucket=bucket, key=key)
            yield self.create_text_message(error_message)
        except Exception as exc:
            error_message = handle_r2_client_error(exc, "delete", bucket=bucket, key=key)
            yield self.create_text_message(error_message)




