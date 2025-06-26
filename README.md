# AstrBot 精美系统信息面板插件 (SysInfoImg)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-AstrBot-orange.svg)](https://github.com/BennettChina/AstrBot)
[![Author](https://img.shields.io/badge/Author-Binbim-brightgreen.svg)](https://github.com/Binbim)
[![Version](https://img.shields.io/badge/Version-6.1.0-blue.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](https://opensource.org/licenses/MIT)

一个为 [AstrBot](https://github.com/BennettChina/AstrBot) 设计的插件，能够生成一张美观、信息丰富的系统状态面板图片，直观展示服务器和机器人核心的运行状态。

## 🙏 致谢

本插件是在 [astrbot_plugin_sysinfo](https://github.com/AstrBot-Devs/astrbot_plugin_sysinfo) 的基础上进行修改和优化的。感谢原作者的贡献！

## ✨ 功能亮点

*   **美观的可视化界面**：使用现代卡片式布局和甜甜圈图，数据一目了然。
*   **全面的系统监控**：
    *   **CPU**：实时使用率、处理器型号、核心/线程数。
    *   **内存**：实时使用率、已用/总容量。
    *   **磁盘**：主分区使用率、已用/总容量。
    *   **系统**：操作系统版本、Python环境、系统总运行时长、网络IO。
*   **专注的机器人状态**：
    *   **Bot运行时长**：插件自包含计时逻辑，精准可靠。
    *   **核心指标**：已加载插件数、连接的平台数、处理的消息总数、Bot进程内存占用。
*   **跨平台兼容**：自动检测并加载 Windows, macOS, Linux 系统下的常用中文字体。
*   **高可靠性**：内置完整的异常处理和日志记录，确保插件稳定运行。
*   **零配置**：即插即用，无需任何额外配置。

## 🎨 效果预览

通过简单的命令，插件会生成并发送如下样式的状态面板：

*(此为根据代码逻辑生成的模拟效果图)*
  <!-- 建议您生成一张实际图片并替换此链接 -->


## 🚀 安装指南

1.  **下载插件文件**：
    *   将 `main.py` 文件放入您的 AstrBot 插件目录（例如 `astrbot/plugins/`）。

2.  **放置背景资源 (可选)**：
    *   插件会尝试加载同目录下的 `background.png` 文件作为背景。您可以放置自己喜欢的图片，或不放置任何文件，插件将自动生成一个简约的渐变背景。

3.  **安装依赖库**：
    插件需要 `psutil` 和 `Pillow` 库来获取系统信息和绘制图片。打开终端或命令提示符，运行以下命令：
    ```bash
    pip install psutil Pillow
    ```

4.  **安装中文字体 (重要)**：
    为了正常显示中文，您的服务器需要安装至少一种支持中文的 TrueType 字体。插件会自动在以下路径寻找字体：
    *   **Windows**: `C:/Windows/Fonts/msyh.ttc` (微软雅黑)
    *   **macOS**: `/System/Library/Fonts/PingFang.ttc` (苹方)
    *   **Linux**:
        *   `/usr/share/fonts/truetype/wqy/wqy-microhei.ttc` (文泉驿微米黑)
        *   `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc` (Noto Sans CJK)

    **如果您的系统没有以上字体**，请手动安装任一中文字体，或修改 `main.py` 文件中 `_load_fonts` 函数内的字体路径。如果所有预设字体都找不到，插件将回退到 PIL 的默认字体，可能导致中文显示为方框 `□`。

5.  **重启 AstrBot**：
    重启您的 AstrBot 程序，插件将会被自动加载。您应该会在日志中看到类似 "精美系统信息面板插件已初始化" 的消息。

## 📝 使用方法

安装并启用插件后，在任何支持的聊天平台中向机器人发送以下命令即可：

**指令**： `sysinfo`

机器人将会回复一张包含最新系统状态的图片。

## 💡 设计说明

### 自包含的 Bot 运行时长

为了提高插件的独立性和兼容性，Bot 的运行时长计算方式从依赖 AstrBot 框架的启动时间，改为**记录插件自身加载的精确时间** (`self.plugin_start_time`)。

这确保了即使在框架API变动或无法获取全局启动时间的情况下，"Bot 运行时长" 这一指标依然能够准确反映当前插件会话的持续时间，增强了插件的健壮性。

## 📄 许可证

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 授权。