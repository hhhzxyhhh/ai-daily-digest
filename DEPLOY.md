# GitHub 部署指南

由于检测到您的环境中未安装 Git 命令行工具，请按照以下步骤手动将项目部署到 GitHub。

## 第一步：安装 Git

1. 访问 [Git 官网下载页面](https://git-scm.com/downloads)
2. 下载适用于 Windows 的安装程序
3. 运行安装程序，一路点击 "Next" 完成安装
4. **重要**：安装完成后，请重启您的终端或编辑器（VS Code/Cursor），以便使环境变量生效

## 第二步：初始化本地仓库

安装完 Git 后，您可以选择以下两种方式之一：

### 方式 A：使用自动脚本（推荐）
在终端中运行以下命令：
```powershell
.\scripts\setup_git.ps1
```
该脚本会自动初始化仓库并提交所有文件。

### 方式 B：手动执行命令
如果您更喜欢手动操作，请依次运行：
```bash
git init
git add .
git commit -m "Initial commit"
```

## 第三步：推送到 GitHub

1. 登录 GitHub，点击右上角的 `+` 号，选择 **New repository**
2. 输入仓库名称（例如 `ai-daily-digest`），保持 Public 或 Private，点击 **Create repository**
3. 在创建完成的页面中，复制 **"…or push an existing repository from the command line"** 下方的代码
4. 回到终端，粘贴并运行这几行代码：

```bash
git remote add origin https://github.com/您的用户名/仓库名.git
git branch -M main
git push -u origin main
```

## 第四步：配置 GitHub Actions（可选）

项目已包含 `.github/workflows/daily-digest.yml` 配置文件。代码推送到 GitHub 后：

1. 进入仓库的 **Settings** -> **Secrets and variables** -> **Actions**
2. 点击 **New repository secret**
3. 添加必要的环境变量（如 `QWEN_API_KEY`, `EMAIL_PASSWORD` 等），详见 `README.md`
4. 提交后，GitHub Actions 将会自动按计划运行
