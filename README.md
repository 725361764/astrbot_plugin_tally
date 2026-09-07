---

## 📦 插件完整文档

### 仓库管理员 (astrbot_plugin_tally)

---

#### 简介

**仓库管理员**是一款支持**多用户数据隔离**的轻量级库存与数据管理工具。每个用户拥有独立的数据空间，支持对任意物品或项目进行**入库（记录）**、**出库（扣减，允许为负数）**、**查看完整操作日志**和**导出 Excel 报表**等操作。每次变动都会记录时间、变动量和剩余量，方便追踪。

**适用场景**：
- 📦 仓库库存管理（允许欠账/负库存）
- ✅ 每日打卡签到
- 📊 积分统计（可透支）
- 📝 物品借用记录
- 🤝 团队协作数据追踪

---

#### 功能概览

**用户管理（多用户隔离）**
- `新增用户名` — 创建新用户并自动绑定到当前账号
- `绑定用户名` — 将当前账号绑定到已存在的用户名
- `解除绑定` — 解除当前账号与用户名的绑定
- `删除用户名` — 永久删除用户及其所有数据

**仓库管理**
- `记录` — 增加物品库存数量（入库）
- `扣减` — 减少物品库存数量（允许为负数）
- `添加` — 新增物品到仓库清单
- `表格` — 查看最近 20 条操作记录
- `导出` — 导出全部记录为 Excel，并上传至远程服务器生成带密码的下载链接
- `记录帮助` / `帮助` / `菜单` — 显示帮助信息

---

#### 安装方法

1. 在 `AstrBot/data/plugins/` 目录下创建插件文件夹：
   ```bash
   mkdir astrbot_plugin_tally
   cd astrbot_plugin_tally
   ```

2. 将以下文件放入该文件夹：
   - `main.py`（主程序）
   - `metadata.yaml`（元数据）
   - `requirements.txt`（依赖）
   - `_conf_schema.json`（配置项定义）
   - `logo.png`（可选，插件图标）

3. 安装依赖：
   ```bash
   pip install openpyxl aiohttp
   ```

4. 在 AstrBot WebUI 中启用该插件。

5. 进入插件配置页面，设置：
   - **上传地址**：`https://xlsx.725361764.cn/upload.php`
   - **API 令牌**：与服务器端 `config.php` 中的 `API_TOKEN` 一致
   - **有效期**：`24`（小时）

---

#### 指令列表

| 指令 | 功能 | 示例 |
|------|------|------|
| `新增用户名 用户名` | 创建新账户并绑定当前账号 | `新增用户名 张三` |
| `绑定用户名 用户名` | 绑定到已存在的账户 | `绑定用户名 张三` |
| `解除绑定` | 解除当前账号的绑定 | `解除绑定` |
| `删除用户名 用户名` | 永久删除账户（⚠️不可恢复） | `删除用户名 张三` |
| `记录 名称 数量` | 增加物品库存（入库） | `记录 美顺 1` |
| `扣减 名称 数量` | 减少物品库存（允许为负数） | `扣减 美顺 1` |
| `添加 名称` | 新增物品到仓库 | `添加 苹果` |
| `表格` | 查看最近 20 条操作记录 | `表格` |
| `导出` | 导出全部记录，生成远程下载链接 | `导出` |
| `记录帮助` / `帮助` / `菜单` | 显示帮助信息 | `记录帮助` |

---

#### 数据存储结构

数据保存在 `data/plugin_data/astrbot_plugin_tally/` 目录下：

**`bindings.json`（绑定关系）**
```json
{
  "725361764": "张三",
  "3372886417": "张三"
}
```

**`tally_data.json`（用户数据）**
```json
{
  "张三": {
    "counts": {
      "美顺": 1,
      "苹果": -1
    },
    "history": [
      {
        "time": "2026-09-04 10:05:15",
        "name": "美顺",
        "change": 0,
        "remain": 0
      },
      {
        "time": "2026-09-04 10:05:42",
        "name": "美顺",
        "change": 1,
        "remain": 1
      }
    ]
  }
}
```

---

#### 插件配置项（`_conf_schema.json`）

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `upload_url` | string | `https://xlsx.725361764.cn/upload.php` | 文件上传服务器地址 |
| `api_token` | string | `your-secret-token-here` | API 安全令牌（需与服务器端一致） |
| `expire_hours` | int | `24` | 下载链接有效期（小时） |

---

#### 从 v1 升级到 v2.x

1. 覆盖 `main.py`、`metadata.yaml`、`requirements.txt`
2. 运行 `pip install openpyxl aiohttp`
3. 重载插件后，**发送 `绑定用户名 default`** 恢复旧数据
4. 继续使用 `记录`、`扣减` 等命令

---

#### 版本信息

| 项目 | 内容 |
|------|------|
| 插件名称 | 仓库管理员 |
| 版本 | 3.0.4 |
| 作者 | 请叫我大王 |
| 仓库地址 | https://github.com/725361764/astrbot_plugin_tally |
| 适配 AstrBot 版本 | >=4.9.2 |
| 分类 | 工具 |

---

#### 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| **3.0.4** | 2026-09-04 | 🎨 优化导出功能，支持远程上传；新增配置项；修复 SSL 证书验证问题；优化表格显示（仅显示最近 20 条） |
| 3.0.0 | 2026-08-12 | ✨ 新增 Web 面板支持；优化导出文件上传逻辑 |
| 2.0.1 | 2026-08-08 | 🐛 修复扣减不能为负数的问题 |
| 2.0.0 | 2026-08-07 | 🎉 重构：多用户隔离、用户管理指令 |
| 1.0.0 | 2026-08-06 | 🎉 初始版本 |

---

#### 常见问题

**Q：首次使用应该先做什么？**
发送 `新增用户名 你的名字` 创建用户并绑定。

**Q：如何在多个 QQ 上共享数据？**
在每个 QQ 上发送 `绑定用户名 相同的用户名` 即可共享。

**Q：导出的 Excel 文件在哪里？**
发送 `导出` 后，插件会生成 Excel 并上传至远程服务器，返回带密码的下载链接，有效期 24 小时。

**Q：为什么表格只显示最近 20 条？**
为防止刷屏，表格仅显示最近 20 条操作记录。完整数据可通过 `导出` 获取。

**Q：扣减可以为负数吗？**
可以。v2.0.1 起已移除负数限制，适合积分透支、欠账等场景。

---

#### 反馈与支持

- **作者**：请叫我大王
- **插件仓库**：https://github.com/725361764/astrbot_plugin_tally
- **Web 面板**：https://github.com/725361764/tally-file-sharing-web
- **问题反馈**：欢迎通过 GitHub Issues 提交

---

## 🌐 Web 面板仓库

### 仓库名称
```
tally-file-sharing-web
```

### 完整地址
```
https://github.com/725361764/tally-file-sharing-web
```

### 仓库说明

这是一个为「仓库管理员」插件配套的**二次元风格文件分享站**，提供文件下载页面和状态展示首页。

**包含文件**：
- `index.php` — 二次元风格首页
- `download.php` — 文件下载页面（带密码验证）
- `config.php` — 数据库配置
- `upload.php` — 文件上传接口（供插件调用）
- `cleanup.php` — 过期文件清理脚本

**部署说明**：
1. 克隆仓库到服务器网站根目录
2. 导入数据库表
3. 修改 `config.php` 中的数据库连接和 API 令牌
4. 设置 Cron 定时运行 `cleanup.php`

---

### Web 面板 README.md

```markdown
# ✨ 星尘分享站 · Tally File Sharing Web

> 为「仓库管理员」AstrBot 插件配套的二次元风格文件分享站

![二次元风格](https://img.shields.io/badge/style-二次元-ff69b4)
![PHP](https://img.shields.io/badge/PHP-8.0+-777bb4)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ 特性

- 🎨 二次元风格 UI（粉紫渐变 + 毛玻璃效果）
- 🔐 双因素密码保护（两个汉字密码）
- ⏱ 24 小时自动过期
- 🧹 定时清理过期文件
- 📱 完美适配手机/电脑
- 🚀 与 AstrBot 插件无缝集成

## 📁 文件结构

```
├── index.php          # 首页
├── download.php       # 下载页面
├── config.php         # 配置文件
├── upload.php         # 上传接口
├── cleanup.php        # 清理脚本
└── uploads/           # 文件存储目录
```

## 🚀 快速部署

### 1. 克隆仓库
```bash
git clone https://github.com/725361764/tally-file-sharing-web.git
cd tally-file-sharing-web
```

### 2. 配置数据库
```sql
CREATE TABLE `uploads` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(10) NOT NULL,
  `password` varchar(10) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `filepath` varchar(255) NOT NULL,
  `expire_at` datetime NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `expire_at` (`expire_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3. 修改配置
编辑 `config.php`，填写数据库信息和 API 令牌。

### 4. 设置权限
```bash
mkdir uploads
chmod 755 uploads
chown -R www:www .
```

### 5. 设置定时任务
```bash
0 * * * * php /path/to/cleanup.php
```

## 🔗 配合插件使用

在 AstrBot 插件配置中设置：
- **上传地址**：`https://你的域名/upload.php`
- **API 令牌**：与 `config.php` 中的 `API_TOKEN` 一致

## 📸 预览

![首页预览](https://via.placeholder.com/800x400/ffe0f0/ab47bc?text=✨+星尘分享站)

## 📝 许可证

MIT License

## 👤 作者

请叫我大王
```

---

## 📋 总结

| 项目 | 地址 |
|------|------|
| 插件仓库 | https://github.com/725361764/astrbot_plugin_tally |
| Web 面板仓库 | https://github.com/725361764/tally-file-sharing-web |
| 在线演示 | https://xlsx.725361764.cn |

---

