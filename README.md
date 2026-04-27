# Jietu OCR (Go + Wails 重构版)

这是一个使用 Go 和 Wails 框架构建的跨平台原生桌面应用程序，主要功能是截取屏幕并使用本地 OCR（Tesseract）识别其中的文字。界面采用了现代的暗色玻璃拟态（Glassmorphism）设计风格。

## 🌟 功能特性

*   **全屏截图与识别**：一键截取当前主屏幕并自动进行 OCR 文字识别。
*   **本地识别**：基于 `tesseract-ocr` 引擎，支持离线识别，无隐私泄露风险。
*   **深色模式美学**：使用纯 HTML/CSS 构建的轻量级前端，搭配拟态玻璃效果。
*   **极简构建**：无须庞大的 Node.js 依赖即可进行构建发布。

## 🛠️ 环境依赖 (Linux / Ubuntu)

本项目在运行和构建时需要特定的系统底层图形库与 Tesseract 文字识别引擎支持。对于 Ubuntu 24.04 等较新的系统，请确保安装以下依赖：

```bash
sudo apt update
sudo apt install -y \
  libgtk-3-dev \
  libwebkit2gtk-4.1-dev \
  libtesseract-dev \
  tesseract-ocr \
  tesseract-ocr-chi-sim \
  tesseract-ocr-eng
```

> **注意**：较老的 Ubuntu 系统（如 20.04/22.04）可能需要安装 `libwebkit2gtk-4.0-dev`。

同时您需要安装最新的 **Go 环境** (>= 1.21) 以及 **Wails CLI**：
```bash
go install github.com/wailsapp/wails/v2/cmd/wails@latest
```

## 🚀 开发与构建

### 启动实时开发模式
开发模式将提供一个独立的应用程序窗口，当你修改 Go 后端代码或前端 HTML/CSS 时，它将自动热重载。
由于较新的 Linux 系统使用了 webkit2gtk 4.1，我们必须加上对应编译标签：

```bash
~/go/bin/wails dev -tags webkit2_41
```

### 编译为可执行文件
将项目编译为单一二进制文件进行分发：

```bash
# 编译为 Linux x86_64 (64位) 原生程序
~/go/bin/wails build -platform linux/amd64 -tags webkit2_41 -clean

# (可选) 编译为 Linux i386 (32位)
# ~/go/bin/wails build -platform linux/386 -tags webkit2_41 -clean
```
编译成功后，产物位于 `build/bin/jietu`，您可以直接双击运行它！

## 📄 许可证

MIT License