"""
場所: tools/r2_file_uploader.py
内容: Dify ワークフローから受け取ったファイルを指定の R2 バケットへアップロードするツール。
目的: 先行ノードで生成したバイナリ資産を R2 へ安全かつ簡潔に保存し、後続ノードで再利用できるようにする。
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from typing import Any, Optional, TYPE_CHECKING

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


def _sanitize_prefix(prefix: str | None) -> str:
    """キーの先頭や末尾のスラッシュを整理し、空文字でも文字列を返す補助関数。"""
    if not prefix:
        return ""
    return prefix.strip("/ ")


class R2FileUploader(Tool):
    r2_client: Optional[S3Client] = None

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """ファイルを取得し、R2 へアップロードした結果を JSON で返す。"""
        try:
            self.r2_client = initialize_r2_client(self, tool_parameters)
        except Exception as exc:
            yield self.create_text_message(f"Failed to initialize R2 client: {exc}")
            return

        input_file = tool_parameters.get("input_file")
        if not input_file:
            yield self.create_text_message("input_file parameter is required")
            return

        try:
            file_bytes: bytes = input_file.blob  # type: ignore[attr-defined]
        except Exception as exc:
            yield self.create_text_message(f"Failed to read input_file: {exc}")
            return

        bucket_name = tool_parameters.get("bucket_name")
        if not bucket_name:
            yield self.create_text_message("bucket_name parameter is required")
            return

        key_prefix = _sanitize_prefix(tool_parameters.get("key_prefix"))
        requested_key = tool_parameters.get("object_key") or getattr(input_file, "filename", None)
        fallback_key = getattr(input_file, "url", "").rstrip("/").split("/")[-1] if getattr(input_file, "url", None) else None
        object_key = requested_key or fallback_key or f"dify-upload-{uuid.uuid4().hex}"
        object_key = object_key.lstrip("/")
        if key_prefix:
            object_key = f"{key_prefix}/{object_key}"

        content_type = getattr(input_file, "mime_type", None) or "application/octet-stream"

        try:
            self.r2_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=file_bytes,
                ContentType=content_type,
            )
        except ClientError as exc:
            error_message = handle_r2_client_error(exc, "upload", bucket=bucket_name, key=object_key)
            yield self.create_text_message(error_message)
            return
        except Exception as exc:
            error_message = handle_r2_client_error(exc, "upload", bucket=bucket_name, key=object_key)
            yield self.create_text_message(error_message)
            return

        r2_uri = f"r2://{bucket_name}/{object_key}"
        result_payload: dict[str, Any] = {
            "bucket_name": bucket_name,
            "object_key": object_key,
            "r2_uri": r2_uri,
        }

        text_message = None
        if tool_parameters.get("generate_presign_url"):
            expiry_seconds = int(tool_parameters.get("presign_expiry", 3600))
            try:
                presigned_url = self.r2_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": object_key},
                    ExpiresIn=expiry_seconds,
                )
                result_payload["presigned_url"] = presigned_url
                result_payload["presign_expiry"] = expiry_seconds
                text_message = self.create_text_message(presigned_url)
            except Exception as exc:
                error_message = handle_r2_client_error(exc, "generate presigned URL", bucket=bucket_name, key=object_key)
                yield self.create_text_message(f"Upload succeeded but failed to create presigned URL: {error_message}")
                return
        else:
            text_message = self.create_text_message(r2_uri)

        yield self.create_json_message(result_payload)
        if text_message:
            yield text_message



