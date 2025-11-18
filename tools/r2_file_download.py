"""
場所: tools/r2_file_download.py
内容: R2 からファイルを取得し、Dify ワークフロー内で扱えるバイナリおよびメタデータ変数を返すダウンロード専用ツール。
目的: r2_operator の読み込み機能を独立させ、ワークフロー後続ノードへファイルをそのまま渡せるようにする。
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


def _build_metadata_text(metadata: dict[str, Any]) -> str:
    """シンプルなキー=値形式のテキストへ整形する。"""
    lines = []
    for key, value in metadata.items():
        if value is None:
            continue
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


class R2FileDownload(Tool):
    r2_client: Optional[S3Client] = None

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """R2 からファイルを取得し、バイナリとメタデータ（JSON/テキスト）を返す。"""
        try:
            self.r2_client = initialize_r2_client(self, tool_parameters)
        except Exception as exc:
            yield self.create_text_message(f"Failed to initialize R2 client: {exc}")
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

        if not self.r2_client:
            yield self.create_text_message("R2 client is not initialized")
            return

        try:
            response = self.r2_client.get_object(Bucket=bucket, Key=key)
            file_bytes = response["Body"].read()
        except ClientError as exc:
            error_message = handle_r2_client_error(exc, "download", bucket=bucket, key=key)
            yield self.create_text_message(error_message)
            return
        except Exception as exc:
            error_message = handle_r2_client_error(exc, "download", bucket=bucket, key=key)
            yield self.create_text_message(error_message)
            return

        filename = key.split("/")[-1] if key else "downloaded_file"
        content_type = response.get("ContentType") or "application/octet-stream"
        metadata_dict = {
            "bucket": bucket,
            "key": key,
            "content_type": content_type,
            "content_length": response.get("ContentLength"),
            "etag": response.get("ETag"),
            "last_modified": response.get("LastModified").isoformat()
            if response.get("LastModified")
            else None,
            "r2_uri": r2_uri,
        }
        metadata_text = _build_metadata_text(metadata_dict)

        blob_meta = {
            "filename": filename,
            "mime_type": content_type,
            "r2_uri": r2_uri,
        }
        yield self.create_blob_message(file_bytes, meta=blob_meta)

        yield self.create_json_message(metadata_dict)
        yield self.create_text_message(metadata_text or f"bucket: {bucket}\nkey: {key}")



