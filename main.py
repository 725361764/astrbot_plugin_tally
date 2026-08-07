import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

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
        self.bind_file = data_path / "bindings.json"

        logger.info(f"📁 数据文件: {self.data_file}")
        logger.info(f"📁 绑定文件: {self.bind_file}")

        self.bindings: Dict[str, str] = {}
        self.user_data: Dict[str, Dict] = {}

        self._load_bindings()
        self._load_user_data()

    # ==================== 数据加载/保存 ====================

    def _load_bindings(self):
        if self.bind_file.exists():
            try:
                with open(self.bind_file, "r", encoding="utf-8") as f:
                    self.bindings = json.load(f)
            except Exception as e:
                logger.error(f"加载绑定关系失败: {e}")
                self.bindings = {}
        else:
            self.bindings = {}

    def _save_bindings(self):
        try:
            with open(self.bind_file, "w", encoding="utf-8") as f:
                json.dump(self.bindings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存绑定关系失败: {e}")

    def _load_user_data(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
                    self.user_data = data
                else:
                    if isinstance(data, dict) and "counts" in data and "history" in data:
                        self.user_data = {"default": {"counts": data["counts"], "history": data["history"]}}
                    elif isinstance(data, dict):
                        self.user_data = {"default": {"counts": data, "history": []}}
                    else:
                        self.user_data = {}
                    logger.warning("检测到旧数据格式，已迁移到用户 'default'")
                    self._save_user_data()
            except Exception as e:
                logger.error(f"加载用户数据失败: {e}")
                self.user_data = {}
        else:
            self.user_data = {}

    def _save_user_data(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用户数据失败: {e}")

    def _get_user_counts(self, username: str) -> Dict[str, int]:
        if username not in self.user_data:
            self.user_data[username] = {"counts": {}, "history": []}
        return self.user_data[username]["counts"]

    def _get_user_history(self, username: str) -> List[Dict]:
        if username not in self.user_data:
            self.user_data[username] = {"counts": {}, "history": []}
        return self.user_data[username]["history"]

    def _add_history(self, username: str, name: str, change: int, remain: int):
        history = self._get_user_history(username)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history.append({
            "time": now,
            "name": name,
            "change": change,
            "remain": remain
        })
        self._save_user_data()

    def _update_count(self, username: str, name: str, delta: int) -> int:
        counts = self._get_user_counts(username)
        current = counts.get(name, 0)
        new_count = max(current + delta, 0)
        counts[name] = new_count
        self._add_history(username, name, delta, new_count)
        return new_count

    def _add_new_entry(self, username: str, name: str) -> bool:
        counts = self._get_user_counts(username)
        if name in counts:
            return False
        counts[name] = 0
        self._add_history(username, name, 0, 0)
        return True

    def _get_current_user(self, event: AstrMessageEvent) -> Optional[str]:
        sender_id = str(event.get_sender_id())
        return self.bindings.get(sender_id)

    def _delete_user(self, username: str) -> bool:
        if username not in self.user_data:
            return False
        del self.user_data[username]
        self._save_user_data()
        qq_to_remove = [qq for qq, name in self.bindings.items() if name == username]
        for qq in qq_to_remove:
            del self.bindings[qq]
        self._save_bindings()
        return True

    # ==================== 辅助检查 ====================

    async def _ensure_binding(self, event: AstrMessageEvent):
        username = self._get_current_user(event)
        if username is None:
            return None, "⚠️ 您尚未绑定用户名，请先使用「新增用户名 用户名」或「绑定用户名 用户名」"
        return username, None

    # ==================== 指令 ====================

    @filter.command("新增用户名")
    async def add_user(self, event: AstrMessageEvent):
        """
        创建新的仓库管理员账户并绑定到当前账号
        格式：新增用户名 用户名
        """
        message = event.message_str.strip()
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("⚠️ 格式错误，请使用：新增用户名 用户名")
            return
        username = parts[1].strip()
        if not username:
            yield event.plain_result("⚠️ 用户名不能为空")
            return

        sender_id = str(event.get_sender_id())
        if username in self.user_data:
            self.bindings[sender_id] = username
            self._save_bindings()
            yield event.plain_result(f"✅ 用户名「{username}」已存在，已绑定到当前账号")
        else:
            self.user_data[username] = {"counts": {}, "history": []}
            self._save_user_data()
            self.bindings[sender_id] = username
            self._save_bindings()
            yield event.plain_result(f"✅ 已创建并绑定用户名「{username}」")

    @filter.command("绑定用户名")
    async def bind_user(self, event: AstrMessageEvent):
        """
        将当前账号绑定到已存在的仓库管理员账户
        格式：绑定用户名 用户名
        """
        message = event.message_str.strip()
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("⚠️ 格式错误，请使用：绑定用户名 用户名")
            return
        username = parts[1].strip()
        if not username:
            yield event.plain_result("⚠️ 用户名不能为空")
            return

        sender_id = str(event.get_sender_id())
        if username not in self.user_data:
            yield event.plain_result(f"⚠️ 用户名「{username}」不存在，请先使用「新增用户名」创建")
            return

        self.bindings[sender_id] = username
        self._save_bindings()
        yield event.plain_result(f"✅ 已绑定用户名「{username}」")

    @filter.command("解除绑定")
    async def unbind_user(self, event: AstrMessageEvent):
        """
        解除当前账号与仓库管理员账户的绑定
        格式：解除绑定
        """
        sender_id = str(event.get_sender_id())
        if sender_id not in self.bindings:
            yield event.plain_result("⚠️ 您当前未绑定任何用户名")
            return
        username = self.bindings.pop(sender_id)
        self._save_bindings()
        yield event.plain_result(f"✅ 已解除绑定用户名「{username}」")

    @filter.command("删除用户名")
    async def delete_user(self, event: AstrMessageEvent):
        """
        永久删除指定的仓库管理员账户及其所有数据（不可恢复）
        格式：删除用户名 用户名
        """
        message = event.message_str.strip()
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("⚠️ 格式错误，请使用：删除用户名 用户名")
            return
        username = parts[1].strip()
        if not username:
            yield event.plain_result("⚠️ 用户名不能为空")
            return

        if username not in self.user_data:
            yield event.plain_result(f"⚠️ 用户名「{username}」不存在")
            return

        if self._delete_user(username):
            yield event.plain_result(
                f"✅ 已删除用户名「{username}」及其所有数据\n"
                f"⚠️ 已解除所有绑定该用户名的账号绑定"
            )
        else:
            yield event.plain_result(f"⚠️ 删除失败，请重试")

    # ==================== 核心记录指令 ====================

    @filter.command("记录")
    async def record(self, event: AstrMessageEvent):
        """
        增加指定物品或项目的库存数量
        格式：记录 名称 数量
        """
        username, err = await self._ensure_binding(event)
        if username is None:
            yield event.plain_result(err)
            return

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

        new_count = self._update_count(username, name, delta)
        yield event.plain_result(f"✅ 已记录 {name} +{delta}，当前共 {new_count}（用户：{username}）")

    @filter.command("扣减")
    async def deduct(self, event: AstrMessageEvent):
        """
        减少指定物品或项目的库存数量
        格式：扣减 名称 数量
        """
        username, err = await self._ensure_binding(event)
        if username is None:
            yield event.plain_result(err)
            return

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

        counts = self._get_user_counts(username)
        current = counts.get(name, 0)
        if current == 0:
            yield event.plain_result(f"⚠️ {name} 当前数量为 0，无法扣减")
            return

        new_count = self._update_count(username, name, -delta)
        yield event.plain_result(f"✅ 已扣减 {name} {delta}，剩余 {new_count}（用户：{username}）")

    @filter.command("添加")
    async def add_entry(self, event: AstrMessageEvent):
        """
        添加新的物品或项目到仓库清单（初始数量为0）
        格式：添加 名称
        """
        username, err = await self._ensure_binding(event)
        if username is None:
            yield event.plain_result(err)
            return

        message = event.message_str.strip()
        match = re.match(r"^添加\s+([^\s]+)$", message)
        if not match:
            yield event.plain_result("⚠️ 格式错误，请使用：添加 名称")
            return

        name = match.group(1)
        if self._add_new_entry(username, name):
            yield event.plain_result(f"✅ 已添加条目：{name}（当前 0）（用户：{username}）")
        else:
            yield event.plain_result(f"⚠️ 条目「{name}」已存在（用户：{username}）")

    @filter.command("表格")
    async def show_table(self, event: AstrMessageEvent):
        """
        查看当前仓库管理员账户的完整操作记录
        格式：表格
        """
        username, err = await self._ensure_binding(event)
        if username is None:
            yield event.plain_result(err)
            return

        history = self._get_user_history(username)
        if not history:
            yield event.plain_result(f"📋 用户「{username}」没有任何操作记录")
            return

        total = len(history)
        lines = []
        lines.append(f"📊 操作记录（用户：{username}，共{total}条）")
        lines.append("时间 | 名称 | 变动 | 剩余")

        last_date = None
        for rec in history:
            dt = datetime.strptime(rec['time'], "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")
            if date_str != last_date:
                lines.append(f"📅 {date_str}")
                last_date = date_str
            change_str = f"+{rec['change']}" if rec['change'] > 0 else str(rec['change'])
            lines.append(f"{time_str} | {rec['name']} | {change_str} | {rec['remain']}")

        counts = self._get_user_counts(username)
        total_count = sum(counts.values())
        items = ", ".join([f"{k}={v}" for k, v in sorted(counts.items())])
        lines.append(f"📈 总计 {total_count} 个  |  📋 {items}")

        yield event.plain_result("\n".join(lines))

    @filter.command("导出")
    async def export(self, event: AstrMessageEvent):
        """
        将当前仓库管理员账户的完整记录导出为 Excel 文件
        格式：导出
        """
        username, err = await self._ensure_binding(event)
        if username is None:
            yield event.plain_result(err)
            return

        history = self._get_user_history(username)
        if not history:
            yield event.plain_result(f"📋 用户「{username}」暂无记录可导出")
            return

        if Workbook is None:
            yield event.plain_result("⚠️ 导出功能需要安装 openpyxl，请运行：pip install openpyxl")
            return

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "记录"
            ws.append(["日期", "名称", "变动", "剩余"])

            sorted_history = sorted(history, key=lambda x: x['time'])
            for rec in sorted_history:
                date_str = rec['time'].split(' ')[0]
                ws.append([date_str, rec['name'], rec['change'], rec['remain']])

            temp_dir = Path(get_astrbot_data_path()) / "temp"
            temp_dir.mkdir(exist_ok=True)
            filename = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_path = temp_dir / filename
            wb.save(file_path)

            yield event.plain_result(f"✅ 已生成导出文件：{filename}")
            try:
                from astrbot.api.message import FileMessage
                yield FileMessage(path=str(file_path))
            except ImportError:
                yield event.plain_result(f"⚠️ 当前环境不支持自动发送文件，请手动下载：{file_path}")
        except Exception as e:
            logger.error(f"导出失败: {e}")
            yield event.plain_result(f"⚠️ 导出失败：{e}")

    @filter.command("表格帮助")
    @filter.command("帮助")
    @filter.command("菜单")
    async def help(self, event: AstrMessageEvent):
        """
        显示仓库管理员插件的所有命令和使用说明
        """
        help_text = (
            "📖 **仓库管理员 - 使用帮助**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 **用户管理指令**\n"
            "  `新增用户名 用户名` - 创建新账户并绑定当前账号\n"
            "  `绑定用户名 用户名`   - 绑定到已存在的账户\n"
            "  `解除绑定`           - 解除当前账号的绑定\n"
            "  `删除用户名 用户名`   - 永久删除账户（⚠️不可恢复）\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 **仓库管理指令**\n"
            "  `记录 名称 数量` - 增加物品库存（如：记录 美顺 1）\n"
            "  `扣减 名称 数量` - 减少物品库存（如：扣减 美顺 1）\n"
            "  `添加 名称`       - 新增物品到仓库（如：添加 苹果）\n"
            "  `表格`            - 查看完整操作记录\n"
            "  `导出`            - 导出为 Excel 文件\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 提示：不同账号绑定同一用户名可共享数据\n"
            "⚠️ 删除用户名将永久删除所有数据，请谨慎操作\n"
            "📦 仓库地址：https://github.com/725361764/astrbot_plugin_tally\n"
            "👤 作者：请叫我大王"
        )
        yield event.plain_result(help_text)

    async def terminate(self):
        self._save_user_data()
        self._save_bindings()
        logger.info("仓库管理员插件已卸载，数据已保存")
