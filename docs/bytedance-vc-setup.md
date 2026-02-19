# 火山引擎语音识别开通教程

火山引擎是字节跳动的云服务平台，其语音识别（Voice Conversion）服务用于将音频转为文字。

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

**方式一：.env 文件**
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

## 费用说明

| 类型 | 额度/价格 |
|------|---------|
| 新用户免费 | 约 2 万次调用 |
| 按量计费 | ¥4.5/小时起 |

> 新用户赠送的免费额度足够日常个人使用很长时间。

## 常见问题

**Q: 认证失败（401）？**
A: 注意 Authorization header 格式为 `Bearer;token`（分号连接，无空格），不是常见的 `Bearer token`。

**Q: AppID 在哪里找？**
A: 控制台 → 语音技术 → 应用管理 → 应用列表中的 AppID 列。

**Q: 免费额度用完了怎么办？**
A: 会自动切换为按量计费（¥4.5/小时起），也可以购买预付费资源包获得更优价格。

**Q: 支持哪些音频格式？**
A: 支持 mp3、wav、pcm 等常见音频格式。本 skill 使用 mp3 格式。
