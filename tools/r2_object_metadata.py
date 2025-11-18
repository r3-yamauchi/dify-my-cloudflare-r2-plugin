"""
場所: tools/r2_object_metadata.py
内容: R2 オブジェクトのメタデータを取得・更新するツール。
目的: オブジェクトのメタデータを確認・更新できるようにする。
"""

from __future__ import annotations

import json
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


def _parse_metadata_string(metadata_str: str | None) -> dict[str, str]:
    """
    メタデータ文字列をパースする。
    形式: "key1=value1,key2=value2" または JSON文字列
    """
    if not metadata_str:
        return {}
    
    metadata = {}
    try:
        # JSON形式を試す
        parsed = json.loads(metadata_str)
        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}
    except (json.JSONDecodeError, ValueError):
        pass
    
    # key=value形式をパース
    for item in metadata_str.split(","):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            metadata[key.strip()] = value.strip()
    
    return metadata


class R2ObjectMetadata(Tool):
    r2_client: Optional[S3Client] = None

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """R2 オブジェクトのメタデータを取得または更新する。"""
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

        operation = tool_parameters.get("operation", "get")

        try:
            if operation == "update":
                # メタデータを更新
                metadata_str = tool_parameters.get("metadata")
                if not metadata_str:
                    yield self.create_text_message("metadata parameter is required for update operation")
                    return

                metadata = _parse_metadata_string(metadata_str)
                
                # 既存のオブジェクトをコピーしてメタデータを更新
                copy_source = {"Bucket": bucket, "Key": key}
                copy_kwargs = {
                    "Bucket": bucket,
                    "Key": key,
                    "CopySource": copy_source,
                    "Metadata": metadata,
                    "MetadataDirective": "REPLACE",
                }
                
                # ContentTypeが指定されている場合は更新
                content_type = tool_parameters.get("content_type")
                if content_type:
                    copy_kwargs["ContentType"] = content_type
                
                self.r2_client.copy_object(**copy_kwargs)
                
                result_payload = {
                    "bucket": bucket,
                    "key": key,
                    "r2_uri": r2_uri,
                    "operation": "update",
                    "metadata": metadata,
                }
                
                yield self.create_json_message(result_payload)
                yield self.create_text_message(f"Successfully updated metadata for: {r2_uri}")
                
            else:  # get operation
                # メタデータを取得
                response = self.r2_client.head_object(Bucket=bucket, Key=key)
                
                metadata = response.get("Metadata", {})
                metadata_dict = {
                    "bucket": bucket,
                    "key": key,
                    "r2_uri": r2_uri,
                    "content_type": response.get("ContentType"),
                    "content_length": response.get("ContentLength"),
                    "etag": response.get("ETag", "").strip('"'),
                    "last_modified": response.get("LastModified").isoformat() if response.get("LastModified") else None,
                    "metadata": metadata,
                }
                
                yield self.create_json_message(metadata_dict)
                
                # 人間が読める形式のテキストも返す
                lines = [f"Metadata for: {r2_uri}"]
                lines.append(f"Content-Type: {metadata_dict.get('content_type', 'unknown')}")
                lines.append(f"Content-Length: {metadata_dict.get('content_length', 0):,} bytes")
                lines.append(f"Last-Modified: {metadata_dict.get('last_modified', 'unknown')}")
                if metadata:
                    lines.append("\nCustom Metadata:")
                    for k, v in metadata.items():
                        lines.append(f"  {k}: {v}")
                
                yield self.create_text_message("\n".join(lines))
                
        except ClientError as exc:
            error_message = handle_r2_client_error(exc, operation, bucket=bucket, key=key)
            yield self.create_text_message(error_message)
        except Exception as exc:
            error_message = handle_r2_client_error(exc, operation, bucket=bucket, key=key)
            yield self.create_text_message(error_message)

