import asyncio
import time
from datetime import datetime, timedelta

import pyautogui

from astrbot.api.event import filter
from astrbot.api.star import Context, Star, StarTools
from astrbot.core import AstrBotConfig
from astrbot.core.message.components import Poke
from astrbot.core.platform import AstrMessageEvent
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)


class ScreenshotPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.conf = config
        self.plugin_data_dir = StarTools.get_data_dir("astrbot_plugin_screenctrl")
        self.screen_width, self.screen_height = pyautogui.size()
        self.last_trigger_time: dict = {}
        self.tasks: dict[int, asyncio.Task] = {}  # 任务 ID -> Task

    async def _capture(self) -> str:
        save_name = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        save_path = self.plugin_data_dir / save_name
        screenshot = await asyncio.to_thread(pyautogui.screenshot)
        await asyncio.to_thread(screenshot.save, save_path)
        return str(save_path)

    @filter.command("截屏", alias={"截图"})
    async def on_capture(self, event: AstrMessageEvent):
        if not event.is_admin() and self.conf["only_admin"]:
            return
        yield event.image_result(await self._capture())

    @filter.command("连续截屏", alias={"连续截图"})
    async def on_continuous_capture(
        self, event: AstrMessageEvent, count: int = 3, interval: int = 5
    ):
        """连续截屏 <次数> <间隔秒>"""
        if not event.is_admin() and self.conf["only_admin"]:
            return
        count = max(1, min(count, 10))
        interval = max(1, min(interval, 3600))

        task_id = len(self.tasks) + 1

        yield event.plain_result(f"连续截屏#{task_id}(共{count}次, 间隔{interval}秒):")

        async def task():
            try:
                for i in range(count):
                    img_path = await self._capture()
                    await event.send(event.image_result(img_path))
                    if i < count - 1:
                        await asyncio.sleep(interval)
            except asyncio.CancelledError:
                await event.send(
                    event.plain_result(f"连续截屏任务 #{task_id} 已被取消")
                )
                return
            finally:
                self.tasks.pop(task_id, None)

        self.tasks[task_id] = asyncio.create_task(task())

    @filter.event_message_type(filter.EventMessageType.ALL, priority=1)
    async def on_poke(self, event: AiocqhttpMessageEvent):
        """戳一戳截屏"""
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

        # 过滤与自身无关的戳
        if raw_message.get("target_id") != raw_message.get("self_id"):
            return
        group_id: int = raw_message.get("group_id", 0)
        # 冷却机制(防止连戳)
        current_time = time.monotonic()
        last_time = self.last_trigger_time.get(group_id, 0)
        if current_time - last_time < self.conf["poke_cd"]:
            return
        self.last_trigger_time[group_id] = current_time

        yield event.image_result(await self._capture())

    @filter.command("定时截屏", alias={"定时截图"})
    async def on_schedule_capture(self, event: AstrMessageEvent):
        """定时截屏: /定时截屏 HH:MM[:SS]"""
        if not event.is_admin() and self.conf["only_admin"]:
            return
        parts = event.message_str.split()
        if len(parts) < 2:
            yield event.plain_result("用法: /定时截屏 HH:MM[:SS]")
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
        yield event.plain_result(f"已设置定时截屏: {target_dt.strftime('%H:%M:%S')}")
        # 分配任务 ID
        task_id = len(self.tasks) + 1

        async def task():
            try:
                await asyncio.sleep(delay)
                img_path = await self._capture()
                await event.send(event.image_result(img_path))
            except asyncio.CancelledError:
                await event.send(
                    event.plain_result(f"定时截屏任务 #{task_id} 已被取消")
                )
                return
            finally:
                self.tasks.pop(task_id, None)

        self.tasks[task_id] = asyncio.create_task(task())

    async def terminate(self):
        """插件卸载时清理所有未完成的定时任务"""
        for task in list(self.tasks.values()):
            task.cancel()
        self.tasks.clear()
