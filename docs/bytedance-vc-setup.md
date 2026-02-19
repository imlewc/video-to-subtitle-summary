# 火山引擎语音识别开通教程

火山引擎是字节跳动的云服务平台，本 skill 使用其 **音视频字幕生成（VC）** 服务将音频转为文字。

> 官方 API 文档：https://www.volcengine.com/docs/6561/80909

## 步骤 1：注册火山引擎

访问火山引擎控制台：

**https://console.volcengine.com**

使用手机号或邮箱注册账号，完成实名认证。

## 步骤 2：开通语音技术服务

1. 登录控制台后，在顶部搜索栏搜索 **"语音技术"** 或 **"语音识别"**
2. 进入 **语音技术** 产品页面
3. 点击 **开通服务**（如未开通）
4. 阅读并同意服务协议

## 步骤 3：创建应用获取 AppID

1. 在语音技术控制台，进入 **应用管理**
2. 点击 **创建应用**
3. 填写应用信息：
   - **应用名称**：任意，如 `video-subtitle`
   - **应用描述**：可选
4. 创建成功后，在应用列表中找到 **AppID**，复制保存

## 步骤 4：获取 Access Token

1. 在语音技术控制台，进入 **密钥管理** 或 **Token 管理**
2. 找到或生成 **Access Token**
3. 复制并保存 Token

> 注意：不同于其他云服务使用 AccessKey/SecretKey，语音识别 API 使用独立的 Bearer Token 认证。

## 步骤 5：配置环境变量

将获得的 AppID 和 Token 配置到环境变量中：

**方式一：.env 文件（推荐）**
```bash
BYTEDANCE_VC_TOKEN=your_actual_token_here
BYTEDANCE_VC_APPID=your_actual_appid_here
```

**方式二：Shell 配置**
```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
export BYTEDANCE_VC_TOKEN="your_actual_token_here"
export BYTEDANCE_VC_APPID="your_actual_appid_here"
source ~/.zshrc  # 使配置生效
```

## 步骤 6：验证配置

```bash
# 准备一个测试音频文件（mp3格式），然后执行：
curl -s -X POST "https://openspeech.bytedance.com/api/v1/vc/submit?appid=$BYTEDANCE_VC_APPID&language=zh-CN" \
  -H "Content-Type: audio/mpeg" \
  -H "Authorization: Bearer;$BYTEDANCE_VC_TOKEN" \
  --data-binary @test_audio.mp3
```

如果返回 `{"id":"xxx","code":0,"message":"Success"}`，说明配置成功。

> **注意 Authorization 格式：** `Bearer;token`，用分号连接，无空格。这与常见的 `Bearer token`（空格）不同。

## API 参考

本 skill 使用以下两个接口：

### 提交任务（Submit）

```
POST https://openspeech.bytedance.com/api/v1/vc/submit
```

**URL 参数：**

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `appid` | 应用 ID | 是 | - |
| `language` | 语言代码 | 是 | - |
| `words_per_line` | 每行字数上限 | 否 | 46 |
| `max_lines` | 每屏最大行数 | 否 | 1 |
| `use_itn` | 数字/日期转换 | 否 | False |
| `use_punc` | 自动添加标点 | 否 | False |
| `caption_type` | 识别类型 | 否 | auto |

**支持语言：** zh-CN（中文普通话）、yue（粤语）、en-US（英语）、ja-JP（日语）、ko-KR（韩语）等

**提交方式一 — 音频二进制：**
```bash
curl -s -X POST "https://openspeech.bytedance.com/api/v1/vc/submit?appid=$APPID&language=zh-CN" \
  -H "Content-Type: audio/mpeg" \
  -H "Authorization: Bearer;$TOKEN" \
  --data-binary @audio.mp3
```

**提交方式二 — 音频 URL：**
```bash
curl -s -X POST "https://openspeech.bytedance.com/api/v1/vc/submit?appid=$APPID&language=zh-CN" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer;$TOKEN" \
  -d '{"url":"https://example.com/audio.mp3"}'
```

### 查询结果（Query）

```
GET https://openspeech.bytedance.com/api/v1/vc/query
```

**URL 参数：**

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `appid` | 应用 ID | 是 | - |
| `id` | 提交返回的任务 ID | 是 | - |
| `blocking` | 0=非阻塞，1=阻塞等待 | 否 | 1 |

### 响应状态码

| 状态码 | 说明 |
|--------|------|
| 0 | 成功 |
| 2000 | 处理中（等待后重试） |
| 1001 | 参数无效 |
| 1002 | 无访问权限 |
| 1010 | 音频过长 |
| 1013 | 音频为静音 |

### 成功响应示例

```json
{
  "id": "task-id",
  "code": 0,
  "utterances": [
    {
      "text": "识别出的文本内容",
      "start_time": 0,
      "end_time": 3000,
      "words": [...]
    }
  ]
}
```

## 费用说明

| 类型 | 额度/价格 |
|------|---------|
| 新用户免费 | 约 2 万次调用 |
| 按量计费 | ¥4.5/小时起 |

> 新用户赠送的免费额度足够日常个人使用很长时间。

## 常见问题

**Q: 认证失败（401/1002）？**
A: 注意 Authorization header 格式为 `Bearer;token`（分号连接，无空格），不是常见的 `Bearer token`。

**Q: AppID 在哪里找？**
A: 控制台 → 语音技术 → 应用管理 → 应用列表中的 AppID 列。

**Q: 返回 code=2000？**
A: 表示任务处理中，等待 5 秒后重新查询即可。

**Q: 返回 code=1010？**
A: 音频文件过长，尝试分段处理。

**Q: 免费额度用完了怎么办？**
A: 会自动切换为按量计费（¥4.5/小时起），也可以购买预付费资源包获得更优价格。

**Q: 支持哪些音频格式？**
A: 支持 mp3、wav、pcm 等常见音频格式。本 skill 使用 mp3 格式。
