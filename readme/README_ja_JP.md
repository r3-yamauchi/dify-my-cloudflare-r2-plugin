# cloudflare_r2_tools

**作成者:** r3-yamauchi  
**バージョン:** 0.0.1  
**タイプ:** tool

[English](../README.md) | 日本語

## 説明

このプラグインは、DifyワークフローやエージェントからCloudflare R2 Storageとやり取りするためのツールを提供します。R2はS3互換のオブジェクトストレージサービスで、大量の非構造化データを保存・提供できます。

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/r3-yamauchi/dify-my-cloudflare-r2-plugin)

## 概要

Cloudflare R2 Toolsプラグインは、Difyアプリケーションがプラットフォーム内で直接ファイルをアップロード、ダウンロード、管理できるようにする複数のツールを提供します。

含まれるツール:
- **R2 File Uploader** – ワークフローノードからR2バケットにファイルをアップロード
- **R2 File Download** – R2バケットからワークフローノードにファイルをダウンロード
- **R2 Operator** – R2オブジェクトへのテキストの読み書き
- **R2 Bucket List** – R2アカウント内のすべてのバケットを一覧表示
- **R2 Bucket Create** – R2アカウントに新しいバケットを作成
- **R2 Object List** – バケット内のオブジェクトを一覧表示（フィルタリング対応）
- **R2 Object Delete** – バケットからオブジェクトを削除
- **R2 Object Metadata** – オブジェクトのメタデータを取得または更新

## 機能

### R2 File Uploader
先行ノードから受け取ったファイルをCloudflare R2バケットにアップロードします。以下の機能をサポート:
- カスタムオブジェクトキーとキープレフィックス
- オプションの署名付きURL生成
- 自動コンテンツタイプ検出

### R2 File Download
R2バケットからファイルをダウンロードし、ワークフローでバイナリデータとして利用可能にします。以下を返却:
- ファイルバイナリデータ
- ファイルメタデータ（JSON形式）
- 人間が読める形式のメタデータテキスト

### R2 Operator
R2オブジェクトへのテキストの読み書きを行います。以下の機能をサポート:
- 読み込み操作（テキストコンテンツまたは署名付きURLを返却）
- 書き込み操作（UTF-8テキストをアップロード）
- 両操作でのオプションの署名付きURL生成

### R2 Bucket List
R2アカウント内のすべてのバケットを一覧表示します。以下を返却:
- バケット名と作成日時
- バケットの総数

### R2 Bucket Create
R2アカウントに新しいバケットを作成します。以下の機能をサポート:
- バケット名の検証（3-63文字、小文字、数字、ハイフン、ドットのみ）
- 自動リージョン選択（デフォルト: 'auto'）
- 既存バケットのエラーハンドリング

### R2 Object List
バケット内のオブジェクトを高度なフィルタリング機能で一覧表示します。以下の機能をサポート:
- プレフィックスフィルタリング（フォルダ風ナビゲーション）
- デリミタベースのグループ化（フォルダ構造）
- ページネーション対応
- 返却するオブジェクトの最大数指定
- オブジェクトと共通プレフィックス（フォルダ）の両方を返却

### R2 Object Delete
バケットからオブジェクトを削除します。以下の機能をサポート:
- URIベースのオブジェクト指定
- エラーハンドリング付きの安全な削除
- 削除確認の返却

### R2 Object Metadata
オブジェクトのメタデータを取得または更新します。以下の機能をサポート:
- 取得操作: オブジェクトメタデータの取得（コンテンツタイプ、サイズ、カスタムメタデータ）
- 更新操作: カスタムメタデータとコンテンツタイプの更新
- メタデータ形式: key=valueペアまたはJSON文字列

## セットアップ

### 前提条件
- R2が有効なCloudflareアカウント
- R2 APIトークン（Access Key IDとSecret Access Key）
- CloudflareアカウントID
- R2リージョン名（例: `auto`, `wnam`, `enam`, `weur`, `eeur`, `apac`）

### インストール
1. Difyインスタンスにプラグインをインストール
2. （任意）プロバイダーにR2認証情報を設定:
   - Account ID（任意 - 各ツールで上書き可能）
   - Access Key ID（任意 - 各ツールで上書き可能）
   - Secret Access Key（任意 - 各ツールで上書き可能）
   - Region Name（任意 - 未指定の場合は 'auto' がデフォルト、各ツールで上書き可能）

**注意**: プロバイダーの認証情報は全て任意項目です。プロバイダーレベルで設定することも、各ツールで個別に指定することもできます。Region Nameが指定されていない場合、デフォルトで 'auto' が使用されます。

### R2認証情報の取得

#### ステップ1: CloudflareアカウントIDを取得

1. [Cloudflare Dashboard](https://dash.cloudflare.com/)にログイン
2. 右上のアカウントドロップダウンからアカウントを選択
3. 右サイドバーの「Account ID」に表示されます
   - または、R2を表示している時のURLからも確認できます: `https://dash.cloudflare.com/{account_id}/r2/overview`
   - Account IDは32文字の16進数文字列です

#### ステップ2: R2 APIトークンを作成

1. Cloudflareダッシュボードで、左サイドバーから **R2** を選択
2. **Manage R2 API Tokens**（または **Settings** → **R2 API Tokens**）をクリック
3. **Create API Token** をクリック
4. トークンを設定:
   - **Token name**: わかりやすい名前を付けます（例: "Dify R2 Tools"）
   - **Permissions**: **Object Read & Write**（バケット管理が必要な場合は **Admin Read & Write**）を選択
   - **TTL**（任意）: 有効期限を設定するか、空白のままにすると無期限
   - **Allowlist IPs**（任意）: 必要に応じて特定のIPアドレスからのアクセスのみを許可
5. **Create API Token** をクリック
6. **重要**: 以下の2つの値をすぐにコピーしてください:
   - **Access Key ID**: `a1b2c3d4...` のような文字列
   - **Secret Access Key**: より長い文字列 - **この値は一度しか表示されません！** 安全に保存してください。

#### ステップ3: R2リージョン名を確認

リージョン名は、R2バケットが配置されている場所によって異なります:
- **auto**: 自動（デフォルト、推奨）
- **wnam**: 西部北米
- **enam**: 東部北米
- **weur**: 西部ヨーロッパ
- **eeur**: 東部ヨーロッパ
- **apac**: アジア太平洋

R2バケットの設定でリージョンを確認できます。または、自動リージョン選択の場合は `auto` を使用してください。

#### ステップ4: Difyで設定

1. Difyで、**Settings** → **Plugins** → **Tool Providers** に移動
2. **Cloudflare R2 Tools** を見つけて **Configure**（または **Add**）をクリック
3. 以下の認証情報を入力:
   - **Cloudflare Account ID**: ステップ1で取得したAccount ID
   - **R2 Access Key ID**: ステップ2で取得したAccess Key ID
   - **R2 Secret Access Key**: ステップ2で取得したSecret Access Key
   - **R2 Region Name**: ステップ3で確認したリージョン名（例: `auto`）
4. **Save** または **Test Connection** をクリックして、認証情報が正しく動作することを確認

## 使用方法

### R2 File Uploader
ファイルをR2にアップロード:
- **bucket_name**: R2バケット名
- **input_file**: アップロードするファイル（ワークフローノードから）
- **object_key** (任意): カスタムオブジェクトキー
- **key_prefix** (任意): フォルダ風プレフィックス
- **generate_presign_url** (任意): 署名付きURLを生成
- **presign_expiry** (任意): 署名付きURLの有効期限（秒）

### R2 File Download
R2からファイルをダウンロード:
- **r2_uri**: `r2://bucket/key` 形式のR2 URI（互換性のため `s3://bucket/key` も可）

### R2 Operator
R2へのテキストの読み書き:
- **r2_uri**: `r2://bucket/key` 形式のR2 URI
- **operation_type**: `read` または `write`
- **text_content** (write時): 書き込むテキスト内容
- **generate_presign_url** (任意): 署名付きURLを生成
- **presign_expiry** (任意): 署名付きURLの有効期限（秒）

### R2 Bucket List
R2アカウント内のすべてのバケットを一覧表示:
- パラメータ不要（プロバイダー認証情報を使用）

### R2 Bucket Create
新しいバケットを作成:
- **bucket_name**: 新しいバケットの名前（3-63文字、小文字、数字、ハイフン、ドットのみ）

### R2 Object List
バケット内のオブジェクトを一覧表示:
- **bucket_name**: R2バケット名
- **prefix** (任意): プレフィックスでオブジェクトをフィルタリング（例: "folder/"）
- **max_keys** (任意): 返却するオブジェクトの最大数（デフォルト: 100）
- **use_delimiter** (任意): デリミタ/フォルダ構造でオブジェクトをグループ化（デフォルト: true）
- **delimiter** (任意): キーをグループ化するために使用する文字（デフォルト: "/"）

### R2 Object Delete
バケットからオブジェクトを削除:
- **r2_uri**: `r2://bucket/key` 形式のR2 URI（互換性のため `s3://bucket/key` も可）

### R2 Object Metadata
オブジェクトのメタデータを取得または更新:
- **r2_uri**: `r2://bucket/key` 形式のR2 URI
- **operation**: `get` または `update`
- **metadata** (update時): 更新するメタデータ（"key1=value1,key2=value2" または JSON形式）
- **content_type** (update時、任意): 更新するコンテンツタイプ（例: "text/plain", "image/png"）

## URI形式

プラグインは互換性のため、`r2://bucket/key` と `s3://bucket/key` の両方のURI形式を受け付けます。`r2://` 形式を推奨します。

## ライセンスと帰属

このプロジェクトはApache License 2.0の下で配布されています。全文については `LICENSE` を、帰属要件については `NOTICE` を参照してください。

## プライバシーポリシー

このプラグインがデータをどのように処理するかについては、`PRIVACY.md` を参照してください。



