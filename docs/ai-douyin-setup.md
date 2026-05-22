# AI Douyin 代理配置指南

AI Douyin 是本 Skill 推荐的视频解析/下载代理，适合不想单独注册 TikHub 的用户。

## 适用场景

- 处理抖音、小红书、B 站等链接时，需要先解析视频下载直链。
- 你不想自行申请 TikHub Token，或者想先使用平台免费额度试用。
- YouTube 不需要 AI Douyin，仍优先使用 `yt-dlp` 直接抓字幕。

## 获取 API Key

1. 打开 [https://ai-douyin.top9.cc](https://ai-douyin.top9.cc)
2. 注册/登录账号。
3. 领取新用户免费额度。
4. 在后台创建 API Key。
5. 在本 Skill 的 `.env` 中填入：

```bash
VIDEO_INFO_PROVIDER=ai-douyin
AI_DOUYIN_API_BASE=https://ai-douyin.top9.cc
AI_DOUYIN_API_KEY=sk_xxx
```

## 计费规则

调用 `POST /api/v1/video/download-url` 成功解析出下载直链后扣 1 积分；解析失败不扣。余额不足时接口返回 HTTP `402`，错误语义为 `insufficient balance`。

## 调用示例

```bash
curl -sS -X POST "https://ai-douyin.top9.cc/api/v1/video/download-url" \
  -H "X-API-Key: sk_xxx" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://v.douyin.com/xxxxxx/"}'
```

成功响应包含：

```json
{
  "download_url": "https://...",
  "extracted_url": "https://v.douyin.com/xxxxxx/",
  "cost": 1
}
```

## 故障处理

- `401`：API Key 缺失或无效。重新复制后台创建的 `sk_...` Key。
- `402 insufficient balance`：免费额度用完或余额不足。可在 AI Douyin 充值积分，或切换为自有 TikHub Token。
- `5xx`：视频平台解析失败或代理服务暂时异常。可稍后重试；如果配置了 `TIKHUB_TOKEN`，可把 `VIDEO_INFO_PROVIDER` 改为 `tikhub` 自行解析。

## 使用自有 TikHub

高级用户也可以绕过 AI Douyin，直接配置：

```bash
VIDEO_INFO_PROVIDER=tikhub
TIKHUB_TOKEN=your_tikhub_api_token
```
