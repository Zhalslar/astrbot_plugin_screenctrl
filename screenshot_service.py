import asyncio
import importlib
from datetime import datetime
from pathlib import Path


class ScreenshotService:
    """
    截图服务（多后端自适应）

    优先级：
    1. mss
    2. PIL.ImageGrab
    3. pyautogui
    4. scrot / grim
    """

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self._mss = None
        self._imagegrab = None
        self._pyautogui = None

    async def capture(self) -> str:
        """
        执行截图并返回文件路径
        """
        save_name = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        save_path = self.temp_dir / save_name
        for backend in (
            self._capture_mss,
            self._capture_pil,
            self._capture_pyautogui,
            self._capture_system,
        ):
            try:
                result = await backend(save_path)
                if result:
                    return result
            except Exception:
                continue
        raise RuntimeError(
            "截图失败：无可用截图后端，请检查 DISPLAY / Wayland / 依赖（mss/scrot/grim）"
        )

    # ====================
    # 各后端实现
    # ====================

    async def _capture_mss(self, save_path: Path) -> str | None:
        """mss"""
        try:
            if self._mss is None:
                self._mss = importlib.import_module("mss")

            def _run():
                with self._mss.mss() as sct:  # type: ignore
                    sct.shot(output=str(save_path))

            await asyncio.to_thread(_run)
            return str(save_path) if save_path.exists() else None
        except Exception:
            return None

    async def _capture_pil(self, save_path: Path) -> str | None:
        """PIL.ImageGrab"""
        try:
            if self._imagegrab is None:
                self._imagegrab = importlib.import_module("PIL.ImageGrab")

            def _run():
                img = self._imagegrab.grab()  # type: ignore
                img.save(save_path)

            await asyncio.to_thread(_run)
            return str(save_path) if save_path.exists() else None
        except Exception:
            return None

    async def _capture_pyautogui(self, save_path: Path) -> str | None:
        """pyautogui"""
        try:
            if self._pyautogui is None:
                self._pyautogui = importlib.import_module("pyautogui")

            def _run():
                screenshot = self._pyautogui.screenshot()  # type: ignore
                screenshot.save(save_path)

            await asyncio.to_thread(_run)
            return str(save_path) if save_path.exists() else None
        except Exception:
            return None

    async def _capture_system(self, save_path: Path) -> str | None:
        """fallback（scrot / grim）"""

        # X11
        try:
            proc = await asyncio.create_subprocess_exec(
                "scrot",
                str(save_path),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            if save_path.exists():
                return str(save_path)
        except Exception:
            pass

        # Wayland
        try:
            proc = await asyncio.create_subprocess_exec(
                "grim",
                str(save_path),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            if save_path.exists():
                return str(save_path)
        except Exception:
            pass

        return None
