"""
場所: tools/r2_object_list.py
内容: R2 バケット内のオブジェクト一覧を取得するツール。
目的: バケット内のオブジェクトを一覧表示し、ワークフローで選択できるようにする。
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


class R2ObjectList(Tool):
    r2_client: Optional[S3Client] = None

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """R2 バケット内のオブジェクト一覧を取得し、JSON形式で返す。"""
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

        prefix = tool_parameters.get("prefix", "").strip("/")
        max_keys = int(tool_parameters.get("max_keys", 100))
        use_delimiter = tool_parameters.get("use_delimiter", True)
        delimiter = tool_parameters.get("delimiter", "/") if use_delimiter else None

        try:
            list_kwargs: dict[str, Any] = {
                "Bucket": bucket_name,
                "MaxKeys": max_keys,
            }
            
            if prefix:
                list_kwargs["Prefix"] = prefix
            if delimiter:
                list_kwargs["Delimiter"] = delimiter
            
            response = self.r2_client.list_objects_v2(**list_kwargs)
            
            objects = []
            for obj in response.get("Contents", []):
                object_info = {
                    "key": obj.get("Key"),
                    "size": obj.get("Size"),
                    "last_modified": obj.get("LastModified").isoformat() if obj.get("LastModified") else None,
                    "etag": obj.get("ETag", "").strip('"'),
                    "r2_uri": f"r2://{bucket_name}/{obj.get('Key')}",
                }
                objects.append(object_info)
            
            # 共通プレフィックス（フォルダ）を取得
            common_prefixes = []
            for prefix_obj in response.get("CommonPrefixes", []):
                prefix_info = {
                    "prefix": prefix_obj.get("Prefix"),
                    "r2_uri": f"r2://{bucket_name}/{prefix_obj.get('Prefix')}",
                }
                common_prefixes.append(prefix_info)
            
            result_payload = {
                "bucket": bucket_name,
                "prefix": prefix if prefix else None,
                "objects": objects,
                "common_prefixes": common_prefixes,
                "object_count": len(objects),
                "prefix_count": len(common_prefixes),
                "is_truncated": response.get("IsTruncated", False),
                "next_continuation_token": response.get("NextContinuationToken"),
            }
            
            yield self.create_json_message(result_payload)
            
            # 人間が読める形式のテキストも返す
            lines = [f"Bucket: {bucket_name}"]
            if prefix:
                lines.append(f"Prefix: {prefix}")
            lines.append(f"Objects: {len(objects)}")
            if common_prefixes:
                lines.append(f"Folders: {len(common_prefixes)}")
            
            if objects:
                lines.append("\nObjects:")
                for obj in objects[:20]:  # 最初の20件のみ表示
                    size = obj.get("size", 0)
                    size_str = f"{size:,} bytes" if size else "unknown size"
                    lines.append(f"  - {obj.get('key')} ({size_str})")
                if len(objects) > 20:
                    lines.append(f"  ... and {len(objects) - 20} more objects")
            
            if common_prefixes:
                lines.append("\nFolders:")
                for prefix_obj in common_prefixes[:10]:  # 最初の10件のみ表示
                    lines.append(f"  - {prefix_obj.get('prefix')}")
                if len(common_prefixes) > 10:
                    lines.append(f"  ... and {len(common_prefixes) - 10} more folders")
            
            yield self.create_text_message("\n".join(lines))
            
        except ClientError as exc:
            error_message = handle_r2_client_error(exc, "list objects", bucket=bucket_name)
            yield self.create_text_message(error_message)
        except Exception as exc:
            error_message = handle_r2_client_error(exc, "list objects", bucket=bucket_name)
            yield self.create_text_message(error_message)

