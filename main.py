import asyncio
import base64
import time
from datetime import datetime, timedelta
from pathlib import Path

import mcp.types

from astrbot.api import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core import AstrBotConfig
from astrbot.core.message.components import BaseMessageComponent, Image, Plain, Poke
from astrbot.core.platform import AstrMessageEvent
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.utils.astrbot_path import get_astrbot_temp_path

from .screenshot_service import ScreenshotService


class ScreenshotPlugin(Star):
    _plugin_name = "astrbot_plugin_screenctrl"

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.conf = config
        self.temp_dir = Path(get_astrbot_temp_path()) / self._plugin_name
        self.service = ScreenshotService(self.temp_dir)

        self.last_trigger_time: dict[int, float] = {}
        self.tasks: dict[int, asyncio.Task] = {}

    async def _capture(self) -> list[BaseMessageComponent]:
        try:
            path = await self.service.capture()
            return [Image.fromFileSystem(path)]
        except Exception as exc:
            logger.error(exc)
            return [Plain(f"截图失败: {exc}")]

    @filter.command("截图", alias={"截屏"})
    async def on_capture(self, event: AstrMessageEvent):
        if not event.is_admin() and self.conf["only_admin"]:
            return
        yield event.chain_result(await self._capture())

    @filter.command("连续截图", alias={"连续截屏"})
    async def on_continuous_capture(
        self, event: AstrMessageEvent, count: int = 3, interval: int = 5
    ):
        """连续截图 <次数> <间隔秒数>"""
        if not event.is_admin() and self.conf["only_admin"]:
            return

        count = max(1, min(count, 10))
        interval = max(1, min(interval, 3600))
        task_id = len(self.tasks) + 1

        yield event.plain_result(
            f"连续截图任务 #{task_id} 已创建，共 {count} 次，间隔 {interval} 秒。"
        )

        async def task():
            try:
                for index in range(count):
                    await event.send(event.chain_result(await self._capture()))
                    if index < count - 1:
                        await asyncio.sleep(interval)
            except asyncio.CancelledError:
                await event.send(event.plain_result(f"连续截图任务 #{task_id} 已取消"))
            finally:
                self.tasks.pop(task_id, None)

        self.tasks[task_id] = asyncio.create_task(task())

    @filter.event_message_type(filter.EventMessageType.ALL, priority=1)
    async def on_poke(self, event: AiocqhttpMessageEvent):
        """戳一戳截图"""
        if (
            not self.conf["poke_screenshot"]
            or not event.is_admin()
            and self.conf["only_admin"]
        ):
            return

        raw_message = getattr(event.message_obj, "raw_message", None)
        if (
            not raw_message
            or not event.message_obj.message
            or not isinstance(event.message_obj.message[0], Poke)
        ):
            return

        if raw_message.get("target_id") != raw_message.get("self_id"):
            return

        group_id = int(raw_message.get("group_id", 0))
        current_time = time.monotonic()
        last_time = self.last_trigger_time.get(group_id, 0.0)
        if current_time - last_time < self.conf["poke_cd"]:
            return
        self.last_trigger_time[group_id] = current_time
        yield event.chain_result(await self._capture())

    @filter.command("定时截图", alias={"定时截屏"})
    async def on_schedule_capture(self, event: AstrMessageEvent):
        """定时截图: /定时截图 HH:MM[:SS]"""
        if not event.is_admin() and self.conf["only_admin"]:
            return

        parts = event.message_str.split()
        if len(parts) < 2:
            yield event.plain_result("用法: /定时截图 HH:MM[:SS]")
            return

        target_time = None
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                target_time = datetime.strptime(parts[1], fmt).time()
                break
            except ValueError:
                continue

        if target_time is None:
            yield event.plain_result("时间格式错误，应为 HH:MM 或 HH:MM:SS")
            return

        now = datetime.now()
        target_dt = datetime.combine(now.date(), target_time)
        if target_dt <= now:
            target_dt += timedelta(days=1)

        delay = (target_dt - now).total_seconds()
        task_id = len(self.tasks) + 1
        yield event.plain_result(
            f"定时截图任务 #{task_id} 已设置，将在 {target_dt.strftime('%H:%M:%S')} 执行。"
        )

        async def task():
            try:
                await asyncio.sleep(delay)
                await event.send(event.chain_result(await self._capture()))
            except asyncio.CancelledError:
                await event.send(event.plain_result(f"定时截图任务 #{task_id} 已取消"))
            finally:
                self.tasks.pop(task_id, None)

        self.tasks[task_id] = asyncio.create_task(task())

    @filter.llm_tool()  # type: ignore
    async def get_current_screen(self, event: AstrMessageEvent):
        """查看电脑屏幕内容，即获取当前屏幕截图来判断电脑上正在做什么"""
        if not event.is_admin() and self.conf["only_admin"]:
            return "该用户无权调用截图工具。"
        try:
            image_path = await self.service.capture()
            image_bytes = await asyncio.to_thread(Path(image_path).read_bytes)
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            return mcp.types.CallToolResult(
                content=[
                    mcp.types.ImageContent(
                        type="image",
                        data=image_base64,
                        mimeType="image/png",
                    )
                ]
            )
        except Exception as exc:
            return f"截图失败: {exc}"

    async def terminate(self):
        for task in list(self.tasks.values()):
            task.cancel()
        self.tasks.clear()
