
<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_screenctrl?name=astrbot_plugin_screenctrl&theme=minecraft&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_screenctrl

_✨ 截屏插件 ✨_  

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4%2B-orange.svg)](https://github.com/Soulter/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-Zhalslar-blue)](https://github.com/Zhalslar)

</div>

## 🤝 介绍

支持用命令截屏、连续截屏、定时截屏、戳一戳截屏。 注意本插件需要桌面环境才能使用，无桌面环境的服务器无法使用！

---

## 📦 安装

在 astrbot 的插件市场搜索 astrbot_plugin_screenctrl，点击安装即可。

安装完成后，根据环境补充依赖：

Python 依赖（一般已自动安装）

```bash
pip install mss Pillow
```

Linux 桌面环境（否则可能截图失败）

```bash
sudo apt install scrot   # X11
sudo apt install grim    # Wayland
```

可选（增强兼容）

```bash
pip install pyautogui
```

注意：必须有桌面环境（无 GUI 服务器无法使用）

---

## ⌨️ 使用说明

### 命令表

|     命令      |                说明                |
|:-------------:|:----------------------------------:|
| 截图 / 截屏   | 对当前电脑屏幕进行截图            |
| 连续截图      | 连续截图（次数 间隔秒）           |
| 定时截图      | 在指定时间执行截图                |
| （戳一戳）    | 触发截图（需在配置中开启）        |


### 示例图

<img width="1240" height="404" alt="tmp3A57" src="https://github.com/user-attachments/assets/649ec5ad-ed5a-4bbd-b4b8-7b659029d412" />

## ⌨️ 配置

请前往插件配置面板进行配置

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码

---

### ⚠️ 常见问题

1️⃣ 截图失败 / 无法使用截图功能

请检查：

* 是否有桌面环境（无 GUI 的服务器无法使用）
* 是否设置 DISPLAY（Linux）

echo $DISPLAY

如果为空，可以尝试：

export DISPLAY=:0
export XAUTHORITY=~/.Xauthority

2️⃣ 在 systemd / 后台运行无法截图

请在 service 配置中添加：

Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/你的用户名/.Xauthority

---

## 📌 注意事项

- 想第一时间得到反馈的可以来作者的插件反馈群（QQ群）：460973561（不点star不给进）

## 📌 免责声明

- 本插件仅供学习与交流！ 插件提供远程控制运行 AstrBot 主机屏幕的能力（点击、按键）。尽管限制到仅bot管理员可用，但这仍然是一个极高的安全风险。一旦管理员账号被盗用或被恶意利用，攻击者可以执行任意按键（如 win+r 打开运行窗口，输入 cmd 并执行任意命令），从而完全控制服务器，可能导致数据泄露、服务瘫痪或被用作跳板机。请谨慎使用，防止管理员账号被盗用，滥用或使用不当造成的后果，由使用者自行承担，与插件开发者无关。
