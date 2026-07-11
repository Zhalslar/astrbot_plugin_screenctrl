import asyncio
import importlib
from datetime import datetime
from pathlib import Path

from astrbot.api import logger


class ScreenshotService:
    """
    Screenshot service with automatic backend fallback.

    Backend priority:
    1. mss
    2. PIL.ImageGrab
    3. pyautogui
    4. scrot
    5. grim
    """

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self._mss = None
        self._imagegrab = None
        self._pyautogui = None

    async def capture(self) -> str:
        """
        Capture the screen and return the saved file path.
        """
        save_name = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        save_path = self.temp_dir / save_name
        for backend in (
            self._capture_mss,
            self._capture_pil,
            self._capture_pyautogui,
            self._capture_scrot,
            self._capture_grim,
        ):
            try:
                result = await backend(save_path)
                if result:
                    return result
            except Exception:
                continue
        raise RuntimeError(
            "Screenshot failed: no available backend. Check the desktop session "
            "and screenshot dependencies (mss/scrot/grim)."
        )

    # ====================
    # Backend implementations
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
        except Exception as exc:
            logger.warning("Screenshot backend mss failed: %s", exc, exc_info=True)
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
        except Exception as exc:
            logger.warning(
                "Screenshot backend PIL.ImageGrab failed: %s",
                exc,
                exc_info=True,
            )
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
        except Exception as exc:
            logger.warning(
                "Screenshot backend pyautogui failed: %s", exc, exc_info=True
            )
            return None

    async def _capture_scrot(self, save_path: Path) -> str | None:
        """scrot"""

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
        except Exception as exc:
            logger.warning("Screenshot backend scrot failed: %s", exc, exc_info=True)

        return None

    async def _capture_grim(self, save_path: Path) -> str | None:
        """grim"""
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
        except Exception as exc:
            logger.warning("Screenshot backend grim failed: %s", exc, exc_info=True)

        return None
