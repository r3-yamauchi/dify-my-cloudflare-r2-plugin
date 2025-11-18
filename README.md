# cloudflare_r2_tools

**Author:** r3-yamauchi  
**Version:** 0.0.1  
**Type:** tool

English | [Japanese](https://github.com/r3-yamauchi/dify-my-cloudflare-r2-plugin/blob/main/readme/README_ja_JP.md)

## Description

This plugin provides tools for interacting with Cloudflare R2 Storage from Dify workflows and agents. R2 is an S3-compatible object storage service that allows you to store and serve large amounts of unstructured data.

The source code of this plugin is available in the [GitHub repository](https://github.com/r3-yamauchi/dify-my-cloudflare-r2-plugin).

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/r3-yamauchi/dify-my-cloudflare-r2-plugin)

## Overview

The Cloudflare R2 Tools plugin bundles multiple tools for Cloudflare R2 Storage so that Dify applications can upload, download, and manage files directly inside the platform.

Included tools:
- **R2 File Uploader** – Upload files from workflow nodes to R2 buckets
- **R2 File Download** – Download files from R2 buckets to workflow nodes
- **R2 Operator** – Read and write text content to/from R2 objects
- **R2 Bucket List** – List all buckets in your R2 account
- **R2 Bucket Create** – Create a new bucket in your R2 account
- **R2 Object List** – List objects in a bucket with optional filtering
- **R2 Object Delete** – Delete an object from a bucket
- **R2 Object Metadata** – Get or update object metadata

## Features

### R2 File Uploader
Upload files received from prior workflow nodes to Cloudflare R2 buckets. Supports:
- Custom object keys and key prefixes
- Optional presigned URL generation
- Automatic content type detection

### R2 File Download
Download files from R2 buckets and make them available as binary data in workflows. Returns:
- File binary data
- File metadata (JSON format)
- Human-readable metadata text

### R2 Operator
Read and write text content to/from R2 objects. Supports:
- Read operations (returns text content or presigned URL)
- Write operations (uploads UTF-8 text)
- Optional presigned URL generation for both operations

### R2 Bucket List
List all buckets in your R2 account. Returns:
- Bucket names and creation dates
- Total count of buckets

### R2 Bucket Create
Create a new bucket in your R2 account. Features:
- Bucket name validation (3-63 characters, lowercase letters, numbers, hyphens, and dots)
- Automatic region selection (defaults to 'auto')
- Error handling for existing buckets

### R2 Object List
List objects in a bucket with advanced filtering. Supports:
- Prefix filtering (folder-style navigation)
- Delimiter-based grouping (folder structure)
- Pagination support
- Maximum number of objects to return
- Returns both objects and common prefixes (folders)

### R2 Object Delete
Delete an object from a bucket. Features:
- URI-based object specification
- Safe deletion with error handling
- Returns deletion confirmation

### R2 Object Metadata
Get or update object metadata. Supports:
- Get operation: Retrieve object metadata (content type, size, custom metadata)
- Update operation: Update custom metadata and content type
- Metadata format: key=value pairs or JSON string

## Setup

### Prerequisites
- A Cloudflare account with R2 enabled
- R2 API tokens (Access Key ID and Secret Access Key)
- Your Cloudflare Account ID
- R2 region name (e.g., `auto`, `wnam`, `enam`, `weur`, `eeur`, `apac`)

### Installation
1. Install the plugin in your Dify instance
2. (Optional) Configure the provider with your R2 credentials:
   - Account ID (optional - can be overridden in each tool)
   - Access Key ID (optional - can be overridden in each tool)
   - Secret Access Key (optional - can be overridden in each tool)
   - Region Name (optional - defaults to 'auto' if not specified, can be overridden in each tool)

**Note**: All provider credentials are optional. You can provide them at the provider level for convenience, or specify them individually in each tool. If Region Name is not specified, it will default to 'auto'.

### Getting R2 Credentials

#### Step 1: Get Your Cloudflare Account ID

1. Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Select your account from the account dropdown (top right)
3. Your Account ID is displayed in the right sidebar under "Account ID"
   - Alternatively, you can find it in the URL when viewing R2: `https://dash.cloudflare.com/{account_id}/r2/overview`
   - The Account ID is a 32-character hexadecimal string

#### Step 2: Create R2 API Token

1. In the Cloudflare Dashboard, navigate to **R2** from the left sidebar
2. Click on **Manage R2 API Tokens** (or go to **Settings** → **R2 API Tokens**)
3. Click **Create API Token**
4. Configure the token:
   - **Token name**: Give it a descriptive name (e.g., "Dify R2 Tools")
   - **Permissions**: Select **Object Read & Write** (or **Admin Read & Write** if you need bucket management)
   - **TTL** (optional): Set expiration if needed, or leave blank for no expiration
   - **Allowlist IPs** (optional): Restrict access to specific IP addresses if needed
5. Click **Create API Token**
6. **Important**: Copy both values immediately:
   - **Access Key ID**: A string starting with characters like `a1b2c3d4...`
   - **Secret Access Key**: A longer string - **you can only see this once!** Save it securely.

#### Step 3: Determine R2 Region Name

The region name depends on where your R2 bucket is located:
- **auto**: Automatic (default, recommended)
- **wnam**: Western North America
- **enam**: Eastern North America
- **weur**: Western Europe
- **eeur**: Eastern Europe
- **apac**: Asia Pacific

You can find the region in your R2 bucket settings, or use `auto` for automatic region selection.

#### Step 4: Configure in Dify

1. In Dify, go to **Settings** → **Plugins** → **Tool Providers**
2. Find **Cloudflare R2 Tools** and click **Configure** (or **Add**)
3. Enter the following credentials:
   - **Cloudflare Account ID**: The Account ID from Step 1
   - **R2 Access Key ID**: The Access Key ID from Step 2
   - **R2 Secret Access Key**: The Secret Access Key from Step 2
   - **R2 Region Name**: The region name from Step 3 (e.g., `auto`)
4. Click **Save** or **Test Connection** to verify the credentials work

## Usage

### R2 File Uploader
Upload a file to R2:
- **bucket_name**: The R2 bucket name
- **input_file**: The file to upload (from a workflow node)
- **object_key** (optional): Custom object key
- **key_prefix** (optional): Folder-style prefix
- **generate_presign_url** (optional): Generate a presigned URL
- **presign_expiry** (optional): Presigned URL expiration time in seconds

### R2 File Download
Download a file from R2:
- **r2_uri**: The R2 URI in `r2://bucket/key` format (or `s3://bucket/key` for compatibility)

### R2 Operator
Read or write text to/from R2:
- **r2_uri**: The R2 URI in `r2://bucket/key` format
- **operation_type**: `read` or `write`
- **text_content** (for write): The text content to write
- **generate_presign_url** (optional): Generate a presigned URL
- **presign_expiry** (optional): Presigned URL expiration time in seconds

### R2 Bucket List
List all buckets in your R2 account:
- No parameters required (uses provider credentials)

### R2 Bucket Create
Create a new bucket:
- **bucket_name**: Name for the new bucket (3-63 characters, lowercase letters, numbers, hyphens, and dots only)

### R2 Object List
List objects in a bucket:
- **bucket_name**: The R2 bucket name
- **prefix** (optional): Filter objects by prefix (e.g., "folder/")
- **max_keys** (optional): Maximum number of objects to return (default: 100)
- **use_delimiter** (optional): Group objects by delimiter/folder structure (default: true)
- **delimiter** (optional): Character used to group keys (default: "/")

### R2 Object Delete
Delete an object from a bucket:
- **r2_uri**: The R2 URI in `r2://bucket/key` format (or `s3://bucket/key` for compatibility)

### R2 Object Metadata
Get or update object metadata:
- **r2_uri**: The R2 URI in `r2://bucket/key` format
- **operation**: `get` or `update`
- **metadata** (for update): Metadata to update in "key1=value1,key2=value2" or JSON format
- **content_type** (for update, optional): Content type to update (e.g., "text/plain", "image/png")

## URI Format

The plugin accepts both `r2://bucket/key` and `s3://bucket/key` URI formats for compatibility. The `r2://` format is recommended.

## License & Attribution

This project is distributed under the Apache License 2.0. See `LICENSE` for the full text and `NOTICE` for attribution requirements.

## Privacy Policy

See `PRIVACY.md` for information about how this plugin handles your data.

---

## 日本語

### 説明

このプラグインは、DifyワークフローやエージェントからCloudflare R2 Storageとやり取りするためのツールを提供します。R2はS3互換のオブジェクトストレージサービスで、大量の非構造化データを保存・提供できます。

### 概要

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

### セットアップ

#### 前提条件
- R2が有効なCloudflareアカウント
- R2 APIトークン（Access Key IDとSecret Access Key）
- CloudflareアカウントID
- R2リージョン名（例: `auto`, `wnam`, `enam`, `weur`, `eeur`, `apac`）

#### インストール
1. Difyインスタンスにプラグインをインストール
2. プロバイダーにR2認証情報を設定:
   - Account ID
   - Access Key ID
   - Secret Access Key
   - Region Name

#### R2認証情報の取得
1. [Cloudflare Dashboard](https://dash.cloudflare.com/)にログイン
2. R2 → Manage R2 API Tokens に移動
3. 適切な権限を持つ新しいAPIトークンを作成
4. Access Key IDとSecret Access Keyをコピー
5. R2ダッシュボードのURLまたはアカウント設定からAccount IDを確認

### 使用方法

#### R2 File Uploader
ファイルをR2にアップロード:
- **bucket_name**: R2バケット名
- **input_file**: アップロードするファイル（ワークフローノードから）
- **object_key** (任意): カスタムオブジェクトキー
- **key_prefix** (任意): フォルダ風プレフィックス
- **generate_presign_url** (任意): 署名付きURLを生成
- **presign_expiry** (任意): 署名付きURLの有効期限（秒）

#### R2 File Download
R2からファイルをダウンロード:
- **r2_uri**: `r2://bucket/key` 形式のR2 URI（互換性のため `s3://bucket/key` も可）

#### R2 Operator
R2へのテキストの読み書き:
- **r2_uri**: `r2://bucket/key` 形式のR2 URI
- **operation_type**: `read` または `write`
- **text_content** (write時): 書き込むテキスト内容
- **generate_presign_url** (任意): 署名付きURLを生成
- **presign_expiry** (任意): 署名付きURLの有効期限（秒）

### URI形式

プラグインは互換性のため、`r2://bucket/key` と `s3://bucket/key` の両方のURI形式を受け付けます。`r2://` 形式を推奨します。



