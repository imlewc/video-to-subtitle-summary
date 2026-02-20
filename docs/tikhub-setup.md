# TikHub API 申请教程

TikHub 提供抖音、小红书、TikTok 等短视频平台数据接口，用于获取视频信息和下载地址。

## 步骤 1：注册账号

访问 TikHub 注册页面：

**https://user.tikhub.io/register?referral_code=2lyqStPc**

填写邮箱和密码完成注册。

## 步骤 2：创建 API Token

1. 登录后进入 **用户中心**
2. 在左侧菜单找到 **API Keys** 或 **Token 管理**
3. 点击 **创建新 Token**
4. 设置 Token 信息：
   - **名称**：任意，如 `video-subtitle`
   - **Scope（权限范围）**：选择需要的 API 权限（至少需要抖音、小红书等视频相关接口）
   - **过期时间**：根据需要设置，建议选择较长有效期
5. 点击创建，**复制并保存生成的 Token**（只会显示一次）

## 步骤 3：配置环境变量

将获得的 Token 配置到环境变量中：

**方式一：.env 文件**
```bash
TIKHUB_TOKEN=your_actual_token_here
```

**方式二：Shell 配置**
```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
export TIKHUB_TOKEN="your_actual_token_here"
source ~/.zshrc  # 使配置生效
```

## 步骤 4：验证配置

```bash
curl -s -X GET "https://api.tikhub.io/api/v1/douyin/web/fetch_one_video_by_share_url?share_url=https%3A%2F%2Fv.douyin.com%2FiRNBho6u%2F" \
  -H "Authorization: Bearer $TIKHUB_TOKEN" \
  -H "Accept: application/json" | head -c 200
```

如果返回 JSON 数据（包含视频信息），说明配置成功。

## 费用说明

| 套餐 | 价格 | 额度 |
|------|------|------|
| 免费套餐 | $0 | 100 次/天 |
| 付费套餐 | $0.001/次起 | 按量计费 |

> 免费套餐每日 100 次请求，对于个人使用完全足够。

## 常见问题

**Q: Token 过期了怎么办？**
A: 回到用户中心重新创建一个新 Token 即可。

**Q: API 返回 401 错误？**
A: 检查 Token 是否正确复制，是否已过期。

**Q: API 返回 429 错误？**
A: 超出免费额度限制，等待次日重置或升级付费套餐。
