# 更新日志

## v1.1.2

New Features:

- 引入 `ScreenshotService`，支持多种截图后端（`mss`、`PIL.ImageGrab`、`pyautogui`、`scrot/grim`），并具备自动回退机制。

Bug Fixes:

- 通过添加多级回退机制和更清晰的错误信息，提高在无头或受限环境中截图功能的健壮性。

Enhancements:

- 重构截图处理逻辑，改为使用 AstrBot 的临时路径以及基于消息链的组件，而不是直接返回文件系统中的图片结果。
- 调整 LLM截图工具权限提示文案，以更准确地提示用户权限限制。
