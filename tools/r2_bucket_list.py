"""
場所: tools/r2_bucket_list.py
内容: R2 アカウント内のバケット一覧を取得するツール。
目的: 利用可能なバケットを一覧表示し、ワークフローで選択できるようにする。
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
        mask_credential,
        build_r2_client_kwargs,
    )
except ModuleNotFoundError:  # pragma: no cover
    from provider.utils import (
        initialize_r2_client,
        handle_r2_client_error,
        resolve_r2_credentials,
        mask_credential,
        build_r2_client_kwargs,
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


class R2BucketList(Tool):
    r2_client: Optional[S3Client] = None

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """R2 アカウント内のバケット一覧を取得し、JSON形式で返す。"""
        try:
            self.r2_client = initialize_r2_client(self, tool_parameters)
        except ValueError as exc:
            # 認証情報の不足などの場合
            yield self.create_text_message(f"Failed to initialize R2 client: {exc}")
            return
        except Exception as exc:
            yield self.create_text_message(f"Failed to initialize R2 client: {exc}")
            return

        if not self.r2_client:
            yield self.create_text_message("R2 client is not initialized")
            return

        try:
            response = self.r2_client.list_buckets()
            buckets = response.get("Buckets", [])
            
            bucket_list = []
            for bucket in buckets:
                bucket_info = {
                    "name": bucket.get("Name"),
                    "creation_date": bucket.get("CreationDate").isoformat() if bucket.get("CreationDate") else None,
                }
                bucket_list.append(bucket_info)
            
            result_payload = {
                "buckets": bucket_list,
                "count": len(bucket_list),
            }
            
            yield self.create_json_message(result_payload)
            
            # 人間が読める形式のテキストも返す
            if bucket_list:
                bucket_names = [bucket["name"] for bucket in bucket_list]
                text_message = f"Found {len(bucket_list)} bucket(s):\n" + "\n".join(f"- {name}" for name in bucket_names)
            else:
                text_message = "No buckets found in this R2 account."
            yield self.create_text_message(text_message)
            
        except ClientError as exc:
            # デバッグ情報を追加
            error_code = exc.response.get("Error", {}).get("Code", "Unknown")
            error_message_raw = exc.response.get("Error", {}).get("Message", str(exc))
            status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", "Unknown")
            
            # 使用されている認証情報を取得（マスク済み）
            credentials = resolve_r2_credentials(self, tool_parameters)
            try:
                client_kwargs = build_r2_client_kwargs(credentials)
                endpoint_url = client_kwargs.get("endpoint_url", "Unknown")
            except ValueError:
                endpoint_url = "Could not build endpoint URL (missing credentials)"
            
            # ユーザーフレンドリーなエラーメッセージを取得
            user_message = handle_r2_client_error(exc, "list buckets")
            
            # 詳細なエラー情報を含める
            debug_info = (
                f"\n\n--- Debug Information ---\n"
                f"Error Code: {error_code}\n"
                f"HTTP Status: {status_code}\n"
                f"Raw Error Message: {error_message_raw}\n"
                f"\n--- Credentials Used (masked) ---\n"
                f"Account ID: {mask_credential(credentials.get('account_id'), 8)}\n"
                f"Access Key ID: {mask_credential(credentials.get('access_key_id'), 8)}\n"
                f"Secret Access Key: {mask_credential(credentials.get('secret_access_key'), 4)} (length: {len(credentials.get('secret_access_key', '')) if credentials.get('secret_access_key') else 0})\n"
                f"Region Name: {credentials.get('region_name', 'Not set')}\n"
                f"Endpoint URL: {endpoint_url}"
            )
            yield self.create_text_message(user_message + debug_info)
        except Exception as exc:
            # その他の例外でもデバッグ情報を追加
            error_message = handle_r2_client_error(exc, "list buckets")
            debug_info = f"\n\n--- Debug Information ---\nException Type: {type(exc).__name__}\nException Message: {str(exc)}"
            yield self.create_text_message(error_message + debug_info)


