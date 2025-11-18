# Privacy Policy

This document describes how the **cloudflare_r2_tools** plugin for Dify handles data when you enable its tools. The plugin is designed to interact with Cloudflare R2 Storage service on your behalf. It does not collect analytics or telemetry beyond what is required to fulfill the tool invocations you issue.

## Data Collection
- **User-supplied inputs.** Text prompts, file uploads, bucket names, object keys, metadata, and other parameters that you pass to the tools are sent to the corresponding Cloudflare R2 service only for the purpose of executing that tool invocation.
- **Configuration metadata.** Cloudflare R2 credentials (account ID, access key ID, secret access key, region name) may be provided either at the provider level or per tool. These values stay within the plugin runtime and are forwarded solely to boto3 clients to authenticate requests to Cloudflare R2.
- **Generated outputs.** Responses received from Cloudflare R2 (e.g., file metadata, presigned URLs, file contents, bucket lists, object lists) are returned directly to Dify and are not stored elsewhere by this plugin.
- The plugin does **not** collect personally identifiable information unless included in the data that you explicitly send to the tools.

## Data Usage
- Inputs are transmitted to Cloudflare R2 services strictly to execute the selected tool (e.g., uploading files, downloading files, reading/writing text content, listing buckets/objects, creating buckets, deleting objects, managing metadata).
- Outputs from Cloudflare R2 are returned to the Dify workflow or agent as-is. No secondary processing or analysis is performed beyond light formatting necessary for the Dify UI.
- The plugin does not sell, share, or reuse your data for any other purpose. Data is not used for model training by this plugin.

## Data Storage
- By default, the plugin does **not** store any user inputs or outputs on its own disk.
- Temporary files are written to local storage only for the duration of the request and deleted immediately after completion.
- Any persistent storage happens only when you instruct a tool to do so (e.g., writing a file to R2 via the respective tools). In such cases the data resides in your Cloudflare R2 account under the resources you control.

## Third-party Services
- The plugin communicates exclusively with Cloudflare R2 Storage using the official AWS SDK (boto3) via S3-compatible API. No other third-party APIs are contacted.
- When using R2 tools, the data is transmitted directly to Cloudflare R2 endpoints over HTTPS.

## Security
- All network calls to Cloudflare R2 use HTTPS, and R2 credentials are loaded into boto3 clients only when needed. If you provide credentials via the provider settings, they remain in memory within the plugin runtime and are not persisted.
- It is your responsibility to secure your Cloudflare R2 resources (bucket policies, access keys, etc.). The plugin will operate with whatever permissions the provided credentials allow.

If you have questions or would like to report a privacy concern, please open an issue in your repository or contact the maintainer directly.



