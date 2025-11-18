"""
場所: provider/utils.py
内容: Cloudflare R2 用のユーティリティ関数（認証情報解決、クライアント構築など）。
目的: ツール間で共通して使用する認証情報管理とクライアント初期化ロジックを提供する。
"""

from __future__ import annotations

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from collections.abc import Iterable
from typing import Optional, Dict, Any, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    # 型チェック時のみインポート（mypy_boto3_s3は開発依存としてインストール可能）
    try:
        from mypy_boto3_s3 import S3Client
    except ImportError:
        # mypy_boto3_s3がインストールされていない場合はbotocore.clientのBaseClientを使用
        from botocore.client import BaseClient
        S3Client = BaseClient
else:
    # 実行時はAnyを使用（型チェックのオーバーヘッドを避ける）
    S3Client = Any


CredentialSignature = Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]


def resolve_r2_credentials(tool: Any, tool_parameters: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    プロバイダーレベルの認証情報とツールパラメータをマージし、ツール固有のパラメータを優先する。
    
    Args:
        tool: ツールインスタンス
        tool_parameters: ツールパラメータの辞書
        
    Returns:
        認証情報を含む辞書（account_id, access_key_id, secret_access_key, region_name）
    """
    runtime_credentials = getattr(getattr(tool, 'runtime', None), 'credentials', {}) or {}

    # ツールパラメータで上書き可能（ツールパラメータを優先）
    account_id = tool_parameters.get('account_id') or runtime_credentials.get('account_id')
    access_key_id = tool_parameters.get('access_key_id') or runtime_credentials.get('access_key_id')
    secret_access_key = tool_parameters.get('secret_access_key') or runtime_credentials.get('secret_access_key')
    region_name = tool_parameters.get('region_name') or runtime_credentials.get('region_name') or 'auto'

    return {
        'account_id': account_id,
        'access_key_id': access_key_id,
        'secret_access_key': secret_access_key,
        'region_name': region_name,
    }


def initialize_r2_client(tool: Any, tool_parameters: Dict[str, Any], client_attr_name: str = 'r2_client') -> S3Client:
    """
    R2クライアントを初期化する共通関数。
    認証情報の解決、クライアントのリセット、初期化を一括で行う。
    
    Args:
        tool: ツールインスタンス
        tool_parameters: ツールパラメータの辞書
        client_attr_name: クライアントを保持する属性名（デフォルト: 'r2_client'）
        
    Returns:
        初期化されたboto3 S3クライアント（R2用）
        
    Raises:
        ValueError: 必要な認証情報が不足している場合
        Exception: クライアント初期化に失敗した場合
    """
    credentials = resolve_r2_credentials(tool, tool_parameters)
    reset_clients_on_credential_change(tool, credentials, [client_attr_name])
    
    client = getattr(tool, client_attr_name, None)
    if not client:
        client_kwargs = build_r2_client_kwargs(credentials)
        client = boto3.client("s3", **client_kwargs)
        setattr(tool, client_attr_name, client)
    
    return client  # type: ignore[return-value]


def mask_credential(value: Optional[str], show_chars: int = 4) -> str:
    """
    認証情報の一部をマスクして表示する。
    
    Args:
        value: マスクする値
        show_chars: 表示する文字数（先頭から）
        
    Returns:
        マスクされた文字列
    """
    if not value:
        return "Not set"
    if len(value) <= show_chars:
        return "*" * len(value)
    return value[:show_chars] + "*" * (len(value) - show_chars)


def build_r2_client_kwargs(credentials: Dict[str, Optional[str]]) -> Dict[str, Any]:
    """
    Cloudflare R2 用のboto3クライアント引数を構築する。
    
    Args:
        credentials: 認証情報を含む辞書
        
    Returns:
        boto3クライアント用の引数辞書
        
    Raises:
        ValueError: 必要な認証情報が不足している場合
    """
    kwargs: Dict[str, Any] = {}
    
    account_id = credentials.get('account_id')
    access_key_id = credentials.get('access_key_id')
    secret_access_key = credentials.get('secret_access_key')
    region_name = credentials.get('region_name') or 'auto'
    
    # 必須認証情報のチェック
    missing_credentials = []
    if not account_id:
        missing_credentials.append("account_id")
    if not access_key_id:
        missing_credentials.append("access_key_id")
    if not secret_access_key:
        missing_credentials.append("secret_access_key")
    
    if missing_credentials:
        raise ValueError(
            f"Missing required R2 credentials: {', '.join(missing_credentials)}. "
            "Please provide them in the provider settings or tool parameters."
        )
    
    kwargs['endpoint_url'] = f"https://{account_id}.r2.cloudflarestorage.com"
    kwargs['region_name'] = region_name
    kwargs['aws_access_key_id'] = access_key_id
    kwargs['aws_secret_access_key'] = secret_access_key
    
    # R2用の設定（path-style addressing）
    kwargs['config'] = Config(s3={"addressing_style": "path"})
    
    return kwargs


def build_credential_signature(credentials: Dict[str, Optional[str]]) -> CredentialSignature:
    """
    認証情報の変更を検出するためのシグネチャを生成する。
    
    Args:
        credentials: 認証情報を含む辞書
        
    Returns:
        認証情報を識別するタプル
    """
    return (
        credentials.get('account_id'),
        credentials.get('access_key_id'),
        credentials.get('secret_access_key'),
        credentials.get('region_name'),
    )


def reset_clients_on_credential_change(
    owner: Any,
    credentials: Dict[str, Optional[str]],
    client_attrs: Iterable[str],
    signature_attr: str = '_client_credentials_signature',
) -> None:
    """
    認証情報が変更された場合にキャッシュされたboto3クライアントをリセットする。
    
    Args:
        owner: クライアントを保持するオブジェクト
        credentials: 認証情報を含む辞書
        client_attrs: リセットするクライアント属性名のリスト
        signature_attr: シグネチャを保存する属性名
    """
    signature = build_credential_signature(credentials)
    current_signature = getattr(owner, signature_attr, None)
    if current_signature != signature:
        for attr in client_attrs:
            if hasattr(owner, attr):
                setattr(owner, attr, None)
        setattr(owner, signature_attr, signature)


def handle_r2_client_error(exc: Exception, operation: str, bucket: str | None = None, key: str | None = None) -> str:
    """
    R2クライアントのエラーを処理し、ユーザーフレンドリーなエラーメッセージを返す。
    
    Args:
        exc: 発生した例外
        operation: 実行していた操作（例: "upload", "download", "read", "write"）
        bucket: バケット名（オプション）
        key: オブジェクトキー（オプション）
        
    Returns:
        ユーザーフレンドリーなエラーメッセージ
    """
    if isinstance(exc, ClientError):
        error_code = exc.response.get("Error", {}).get("Code", "")
        error_message = exc.response.get("Error", {}).get("Message", str(exc))
        
        # よくあるエラーコードに対する具体的なメッセージ
        if error_code == "NoSuchBucket":
            if bucket:
                return f"Bucket '{bucket}' does not exist"
            else:
                return "Bucket does not exist"
        elif error_code == "NoSuchKey":
            if bucket:
                return f"Object '{key}' does not exist in bucket '{bucket}'"
            else:
                return f"Object '{key}' does not exist"
        elif error_code == "AccessDenied":
            # より詳細なエラーメッセージを含める
            detailed_msg = f" (Error: {error_message})" if error_message and error_message != str(exc) else ""
            if bucket:
                return f"Access denied to bucket '{bucket}'. Please check your credentials and permissions.{detailed_msg}"
            else:
                # バケット一覧取得の場合、特別なメッセージを追加
                return (
                    f"Access denied. Please check your R2 Access Key ID permissions.{detailed_msg}\n"
                    f"\nNote: The 'list_buckets' operation requires account-level permissions.\n"
                    f"Required permission type: 'Admin Read Only' or 'Admin Read and Write'\n"
                    f"Current permission type may be: 'Object Read and Write' or 'Object Read Only'\n"
                    f"Please update your R2 API token permissions in Cloudflare Dashboard:\n"
                    f"  - Go to R2 → Manage R2 API Tokens\n"
                    f"  - Edit your API token\n"
                    f"  - Change 'Access Permissions' to 'Admin Read Only' or 'Admin Read and Write'"
                )
        elif error_code == "InvalidAccessKeyId":
            return f"Invalid access key ID. Please check your R2 credentials. (Error: {error_message})"
        elif error_code == "SignatureDoesNotMatch":
            return f"Invalid secret access key. Please check your R2 credentials. (Error: {error_message})"
        elif error_code == "403":
            # HTTP 403エラーの場合
            detailed_msg = f" (Error: {error_message})" if error_message and error_message != str(exc) else ""
            return f"Access forbidden (403). Please check your R2 API token permissions.{detailed_msg}"
        else:
            # エラーコードとメッセージの両方を表示
            return f"Failed to {operation} R2 object. Error Code: {error_code}, Message: {error_message}"
    else:
        return f"Failed to {operation} R2 object: {str(exc)}"



