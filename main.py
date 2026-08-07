import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None


class TallyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        data_path = Path(get_astrbot_data_path()) / "plugin_data" / self.name
        data_path.mkdir(parents=True, exist_ok=True)
        self.data_file = data_path / "tally_data.json"
        logger.info(f"📁 数据文件位置: {self.data_file}")

        self.counts: Dict[str, int] = {}
        self.history: List[Dict] = []
        self._load_data()

    def _load_data(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "counts" in data and "history" in data:
                    self.counts = data["counts"]
                    self.history = data["history"]
                else:
                    self.counts = data if isinstance(data, dict) else {}
                    self.history = []
                    for name, count in self.counts.items():
                        self.history.append({
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "name": name,
                            "change": 0,
                            "remain": count
                        })
                    self._save_data()
            except Exception as e:
                logger.error(f"加载数据失败: {e}")
                self.counts = {}
                self.history = []
        else:
            self.counts = {}
            self.history = []

    def _save_data(self):
        try:
            data = {"counts": self.counts, "history": self.history}
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    def _get_current(self, name: str) -> int:
        return self.counts.get(name, 0)

    def _add_history(self, name: str, change: int, remain: int):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append({
            "time": now,
            "name": name,
            "change": change,
            "remain": remain
        })

    def _update_count(self, name: str, delta: int) -> int:
        current = self._get_current(name)
        new_count = max(current + delta, 0)
        self.counts[name] = new_count
        self._add_history(name, delta, new_count)
        self._save_data()
        return new_count

    def _add_new_entry(self, name: str) -> bool:
        if name in self.counts:
            return False
        self.counts[name] = 0
        self._add_history(name, 0, 0)
        self._save_data()
        return True

    def _format_table(self) -> str:
        if not self.history:
            return "📋 当前没有任何操作记录"
        total = len(self.history)
        lines = []
        lines.append(f"📊 操作记录（共{total}条）")
        lines.append("时间 | 名称 | 变动 | 剩余")
        last_date = None
        for rec in self.history:
            dt = datetime.strptime(rec['time'], "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")
            if date_str != last_date:
                lines.append(f"📅 {date_str}")
                last_date = date_str
            change_str = f"+{rec['change']}" if rec['change'] > 0 else str(rec['change'])
            lines.append(f"{time_str} | {rec['name']} | {change_str} | {rec['remain']}")
        total_count = sum(self.counts.values())
        items = ", ".join([f"{k}={v}" for k, v in sorted(self.counts.items())])
        lines.append(f"📈 总计 {total_count} 个  |  📋 {items}")
        return "\n".join(lines)

    def _generate_excel(self) -> Path:
        if Workbook is None:
            raise RuntimeError("请安装 openpyxl 库: pip install openpyxl")
        wb = Workbook()
        ws = wb.active
        ws.title = "记录"
        ws.append(["日期", "名称", "变动", "剩余"])
        sorted_history = sorted(self.history, key=lambda x: x['time'])
        for rec in sorted_history:
            date_str = rec['time'].split(' ')[0]
            ws.append([date_str, rec['name'], rec['change'], rec['remain']])
        temp_dir = Path(get_astrbot_data_path()) / "temp"
        temp_dir.mkdir(exist_ok=True)
        filename = f"记录导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = temp_dir / filename
        wb.save(file_path)
        return file_path

    @filter.command("记录")
    async def record(self, event: AstrMessageEvent):
        message = event.message_str.strip()
        match = re.match(r"^记录\s+([^\s]+)\s+([+-]?\d+)$", message)
        if not match:
            yield event.plain_result("⚠️ 格式错误，请使用：记录 名称 数量")
            return
        name = match.group(1)
        try:
            delta = int(match.group(2))
        except ValueError:
            yield event.plain_result("⚠️ 数量必须是数字")
            return
        if delta <= 0:
            yield event.plain_result("⚠️ 记录时数量必须为正数，如需扣减请使用「扣减」")
            return
        new_count = self._update_count(name, delta)
        yield event.plain_result(f"✅ 已记录 {name} +{delta}，当前 {new_count}")

    @filter.command("扣减")
    async def deduct(self, event: AstrMessageEvent):
        message = event.message_str.strip()
        match = re.match(r"^扣减\s+([^\s]+)\s+(\d+)$", message)
        if not match:
            yield event.plain_result("⚠️ 格式错误，请使用：扣减 名称 数量")
            return
        name = match.group(1)
        try:
            delta = int(match.group(2))
        except ValueError:
            yield event.plain_result("⚠️ 数量必须是数字")
            return
        if delta <= 0:
            yield event.plain_result("⚠️ 扣减数量必须为正数")
            return
        current = self._get_current(name)
        if current == 0:
            yield event.plain_result(f"⚠️ {name} 当前为 0，无法扣减")
            return
        new_count = self._update_count(name, -delta)
        yield event.plain_result(f"✅ 已扣减 {name} {delta}，剩余 {new_count}")

    @filter.command("表格")
    async def show_table(self, event: AstrMessageEvent):
        yield event.plain_result(self._format_table())

    @filter.command("添加")
    async def add_entry(self, event: AstrMessageEvent):
        message = event.message_str.strip()
        match = re.match(r"^添加\s+([^\s]+)$", message)
        if not match:
            yield event.plain_result("⚠️ 格式错误，请使用：添加 名称")
            return
        name = match.group(1)
        if self._add_new_entry(name):
            yield event.plain_result(f"✅ 已添加：{name}（当前 0）")
        else:
            yield event.plain_result(f"⚠️ 条目「{name}」已存在")

    # ========== 修改点：增加多个命令别名 ==========
    @filter.command("表格帮助", "帮助", "菜单")
    async def table_help(self, event: AstrMessageEvent):
        help_text = (
            "📖 **记录插件使用帮助**\n"
            "命令格式：\n"
            "1. `记录 名称 数量` - 增加数量（如：记录 美顺 1）\n"
            "2. `扣减 名称 数量` - 扣减数量（如：扣减 美顺 1）\n"
            "3. `添加 名称` - 添加新条目（如：添加 苹果）\n"
            "4. `表格` - 查看完整操作记录（按日期分组）\n"
            "5. `导出` - 导出完整记录为 Excel 文件\n"
            "6. `帮助` / `菜单` / `表格帮助` - 显示本帮助信息\n"
            "提示：名称中不能包含空格。"
        )
        yield event.plain_result(help_text)

    @filter.command("导出")
    async def export(self, event: AstrMessageEvent):
        if not self.history:
            yield event.plain_result("⚠️ 暂无记录可导出")
            return
        try:
            file_path = self._generate_excel()
            yield event.plain_result(f"✅ 已生成导出文件：{file_path.name}")
            try:
                from astrbot.api.message import FileMessage
                yield FileMessage(path=str(file_path))
            except ImportError:
                yield event.plain_result(f"⚠️ 当前环境不支持自动发送文件，请手动下载：{file_path}")
        except Exception as e:
            logger.error(f"导出失败: {e}")
            yield event.plain_result(f"⚠️ 导出失败：{e}")

    async def terminate(self):
        self._save_data()
        logger.info("记录插件已卸载，数据已保存")
