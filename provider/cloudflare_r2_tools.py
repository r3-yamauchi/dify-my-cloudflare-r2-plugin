from typing import Any

from dify_plugin import ToolProvider


class CloudflareR2ToolsProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """
        Cloudflare R2 の認証情報を検証する。
        全ての認証情報は任意項目として扱われ、各ツールで上書き可能。
        認証情報が提供されていない場合でも、ツール実行時にエラーが発生するため、
        ここでは検証を行わない。
        """
        # 全ての認証情報が任意項目のため、プロバイダーレベルでの検証は行わない
        # 各ツール実行時に必要な認証情報が揃っているか確認される
        pass



