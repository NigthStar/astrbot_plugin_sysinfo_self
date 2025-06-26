# -*- coding: utf-8 -*-
import sys
import psutil
import platform
import datetime
import io
import math
import time
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 确保在Windows控制台下有正确的编码
if sys.platform.startswith('win'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except Exception as e:
        print(f"警告: 无法设置控制台编码为UTF-8: {e}")

# 兼容插件独立运行和在AstrBot框架内运行
try:
    from astrbot.api import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Image as AstrImage, Plain


@register("sysinfoimg", "Binbim", "生成一个精美的系统信息状态面板", "6.1.0 (自包含最终版)")
class SysInfoImgPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # --- NEW: 在插件初始化时，直接记录当前时间作为精确的启动时间 ---
        self.plugin_start_time = datetime.datetime.now()
        logger.info(f"SysInfoImg 插件已启动，精确启动时间已记录: {self.plugin_start_time}")
        
        self.font_main = None
        self.font_bold = None
        self.fonts_loaded = False

    async def initialize(self):
        """异步初始化插件，加载所需字体。"""
        self._load_fonts()
        logger.info("精美系统信息面板插件已初始化")

    def _load_fonts(self):
        """集中管理字体加载，避免重复的磁盘访问。"""
        if self.fonts_loaded: return
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑 (Windows)
            "/System/Library/Fonts/PingFang.ttc", # 苹方 (macOS)
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", # 文泉驿微米黑 (Linux)
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" # Noto Sans CJK
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    self.font_main = ImageFont.truetype(font_path, size=28, index=0)
                    self.font_bold = self.font_main
                    self.fonts_loaded = True
                    logger.info(f"成功加载字体: {font_path}")
                    return
                except Exception as e:
                    logger.warning(f"加载字体失败 {font_path}: {e}")
        logger.error("未能加载任何预设的中文字体，将使用PIL的默认字体。")
        self.font_main = ImageFont.load_default()
        self.font_bold = self.font_main
        self.fonts_loaded = True
        
    def _get_font(self, size, bold=False):
        """辅助函数，用于获取指定大小的字体。"""
        if not self.fonts_loaded: self._load_fonts()
        font_to_use = self.font_bold if bold else self.font_main
        try: return font_to_use.font_variant(size=size)
        except AttributeError: return self.font_main

    def get_system_info(self):
        """收集所有系统和性能相关信息。"""
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk_path = 'C:\\' if platform.system() == 'Windows' else '/'
        disk = psutil.disk_usage(disk_path)
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        net_io = psutil.net_io_counters()
        
        return {
            'os': f"{platform.system()} {platform.release().split('.')[0]}",
            'python_version': f"Python {platform.python_version()}",
            'uptime': f"{uptime.days}天 {uptime.seconds // 3600}小时 {uptime.seconds % 3600 // 60}分钟",
            'net_sent': f"{net_io.bytes_sent / (1024*1024):.1f} MB",
            'net_recv': f"{net_io.bytes_recv / (1024*1024):.1f} MB",
            'cpu_usage': cpu_percent,
            'cpu_model': (psutil.cpu_info().get('brand_raw', '未知') if hasattr(psutil, 'cpu_info') else platform.processor()),
            'cpu_cores': f"{psutil.cpu_count(logical=False)}核{psutil.cpu_count(logical=True)}线程",
            'mem_usage': mem.percent,
            'mem_used': f"{mem.used / (1024**3):.1f} GB",
            'mem_total': f"{mem.total / (1024**3):.1f} GB",
            'disk_usage': disk.percent,
            'disk_used': f"{disk.used / (1024**3):.1f} GB",
            'disk_total': f"{disk.total / (1024**3):.1f} GB",
        }

    def get_astrbot_info(self):
        """获取AstrBot的核心信息 (采用自包含计时逻辑)。"""
        info = {'uptime': "未知", 'message_count': "未知", 'platforms': "未知", 'mem_usage': "未知", 'plugins': "未知"}
        
        # 1. Bot运行时间 (直接使用本插件的启动时间)
        try:
            delta = datetime.datetime.now() - self.plugin_start_time
            m, s = divmod(delta.seconds, 60)
            h, m = divmod(m, 60)
            info['uptime'] = f"{h}小时{m}分{s}秒"
        except Exception as e:
            logger.warning(f"计算插件运行时长失败: {e}")

        # 2. 其他信息 (逻辑保持不变)
        try: info['mem_usage'] = f"{psutil.Process().memory_info().rss >> 20} MB"
        except: pass
        try: info['plugins'] = f"{len(self.context.get_all_stars())} 个"
        except: pass
        try: info['platforms'] = f"{len(self.context.platform_manager.get_insts())} 个"
        except: pass
        try:
            db_helper = self.context.get_db()
            info['message_count'] = f"{db_helper.get_total_message_count() or 0} 条"
        except: pass
            
        return info
        
    def create_system_info_image(self, sys_info, bot_info):
        """创建精美、专注核心信息的系统状态面板。"""
        W, H = 1200, 1050
        
        C_CARD_BG, C_TEXT_MAIN, C_TEXT_SUB, C_TEXT_VALUE, C_DIVIDER, C_CPU_COLOR, C_MEM_COLOR, C_DISK_COLOR, C_LEGEND_FREE = (255, 255, 255, 200), "#2c3e50", "#7f8c8d", "#34495e", "#ecf0f1", "#e74c3c", "#3498db", "#f1c40f", "#bdc3c7"
        
        base = Image.new("RGBA", (W, H))
        try:
            background_image_path = os.path.join(os.path.dirname(__file__), 'background.png')
            if os.path.exists(background_image_path):
                base = Image.open(background_image_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
            else:
                draw_base = ImageDraw.Draw(base)
                for i in range(H):
                    ratio = i / H
                    r, g, b = [int(s + (e - s) * ratio) for s, e in zip((236, 240, 241), (200, 220, 230))]
                    draw_base.line([(0, i), (W, i)], fill=(r, g, b))
        except Exception as e:
            logger.error(f"加载背景时出错: {e}")
            base.paste((220, 220, 230), [0, 0, W, H])

        canvas = Image.new("RGBA", (W, H))
        draw = ImageDraw.Draw(canvas)

        def draw_text(pos, text, size, color=C_TEXT_MAIN, bold=False):
            draw.text(pos, text, font=self._get_font(size, bold), fill=color)

        def draw_icon(icon_name, pos, color):
            x, y = pos
            if icon_name == 'cpu':
                draw.rectangle([(x, y + 5), (x + 30, y + 35)], outline=color, width=3); draw.line([(x + 7, y + 12), (x + 7, y + 28)], fill=color, width=3); draw.line([(x + 15, y + 12), (x + 15, y + 28)], fill=color, width=3); draw.line([(x + 23, y + 12), (x + 23, y + 28)], fill=color, width=3)
            elif icon_name == 'memory':
                draw.rectangle([(x, y + 10), (x + 30, y + 30)], outline=color, width=3); draw.rectangle([(x + 5, y + 15), (x + 25, y + 25)], fill=color)
            elif icon_name == 'disk':
                draw.ellipse([(x, y + 5), (x + 30, y + 35)], outline=color, width=3); draw.ellipse([(x + 8, y + 13), (x + 22, y + 27)], outline=color, width=3)
            elif icon_name == 'system':
                draw.rectangle([(x, y + 5), (x + 30, y + 35)], outline=color, width=3); draw.line([(x, y + 15), (x + 30, y + 15)], fill=color, width=3); draw.line([(x + 5, y + 22), (x + 15, y + 22)], fill=color, width=2)
            elif icon_name == 'bot':
                draw.ellipse([(x + 5, y), (x + 25, y + 20)], fill=color); draw.rectangle([(x, y + 15), (x + 30, y + 40)], fill=color); draw.ellipse([(x + 8, y + 5), (x + 12, y + 9)], fill="white")

        def draw_donut_chart(pos, percentage, color, radius=80):
            cx, cy = pos
            box = [cx - radius, cy - radius, cx + radius, cy + radius]
            draw.arc(box, 0, 360, fill=C_LEGEND_FREE, width=20)
            draw.arc(box, -90, -90 + percentage * 3.6, fill=color, width=20)
            text = f"{percentage:.1f}%"
            bbox = draw.textbbox((0, 0), text, font=self._get_font(32, True))
            draw_text((cx - bbox[2]/2, cy - bbox[3]/2), text, 32, C_TEXT_MAIN, True)

        def draw_info_line(y_pos, x_start, width, label, value):
            draw_text((x_start, y_pos), label, 24, C_TEXT_SUB)
            bbox = draw.textbbox((0,0), str(value), font=self._get_font(24))
            draw_text((x_start + width - bbox[2], y_pos), str(value), 24, C_TEXT_VALUE)
            draw.line([(x_start, y_pos + 38), (x_start+width, y_pos + 38)], fill=C_DIVIDER, width=1)

        def draw_card(pos, size, title, icon_name, icon_color):
            x, y = pos; w, h = size
            draw.rounded_rectangle((x, y, x + w, y + h), radius=20, fill=C_CARD_BG)
            draw_icon(icon_name, (x+30, y+28), icon_color)
            draw_text((x+75, y+30), title, 30, C_TEXT_MAIN, True)
            return (x + 30, y + 90)

        draw_icon('system', (60, 58), C_TEXT_MAIN); draw_text((110, 60), "系统信息面板", 36, C_TEXT_MAIN, True); draw_text((110, 110), f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 22, C_TEXT_SUB)
        card_w_top, card_h_top = 350, 480; padding_top = (W - 3 * card_w_top) / 4; y_top = 180
        
        cx, cy = draw_card((padding_top, y_top), (card_w_top, card_h_top), "CPU 使用率", 'cpu', C_CPU_COLOR); draw_donut_chart((cx + (card_w_top-60)/2, cy+80), sys_info['cpu_usage'], C_CPU_COLOR); draw.ellipse([cx+80, cy+195, cx+95, cy+210], fill=C_CPU_COLOR); draw_text([cx+105, cy+192], "使用中", 20, C_TEXT_SUB); draw.ellipse([cx+190, cy+195, cx+205, cy+210], fill=C_LEGEND_FREE); draw_text([cx+215, cy+192], "空闲", 20, C_TEXT_SUB); draw_info_line(cy+250, cx, card_w_top-60, "处理器型号", sys_info['cpu_model'].split('@')[0].strip()); draw_info_line(cy+300, cx, card_w_top-60, "核心数量", sys_info['cpu_cores'])
        cx, cy = draw_card((padding_top*2 + card_w_top, y_top), (card_w_top, card_h_top), "内存使用率", 'memory', C_MEM_COLOR); draw_donut_chart((cx + (card_w_top-60)/2, cy+80), sys_info['mem_usage'], C_MEM_COLOR); draw.ellipse([cx+80, cy+195, cx+95, cy+210], fill=C_MEM_COLOR); draw_text([cx+105, cy+192], "已使用", 20, C_TEXT_SUB); draw.ellipse([cx+190, cy+195, cx+205, cy+210], fill=C_LEGEND_FREE); draw_text([cx+215, cy+192], "空闲", 20, C_TEXT_SUB); draw_info_line(cy+250, cx, card_w_top-60, "已使用", sys_info['mem_used']); draw_info_line(cy+300, cx, card_w_top-60, "总容量", sys_info['mem_total'])
        cx, cy = draw_card((padding_top*3 + card_w_top*2, y_top), (card_w_top, card_h_top), "磁盘使用率", 'disk', C_DISK_COLOR); draw_donut_chart((cx + (card_w_top-60)/2, cy+80), sys_info['disk_usage'], C_DISK_COLOR); draw.ellipse([cx+80, cy+195, cx+95, cy+210], fill=C_DISK_COLOR); draw_text([cx+105, cy+192], "已使用", 20, C_TEXT_SUB); draw.ellipse([cx+190, cy+195, cx+205, cy+210], fill=C_LEGEND_FREE); draw_text([cx+215, cy+192], "空闲", 20, C_TEXT_SUB); draw_info_line(cy+250, cx, card_w_top-60, "已使用", sys_info['disk_used']); draw_info_line(cy+300, cx, card_w_top-60, "总容量", sys_info['disk_total'])

        y_bot = y_top + card_h_top + 40; card_w_bot, card_h_bot = 525, 330; padding_bot = (W - 2 * card_w_bot) / 3
        cx, cy = draw_card((padding_bot, y_bot), (card_w_bot, card_h_bot), "系统信息", 'system', C_TEXT_MAIN); draw_info_line(cy, cx, card_w_bot-60, "操作系统", sys_info['os']); draw_info_line(cy+50, cx, card_w_bot-60, "Python版本", sys_info['python_version']); draw_info_line(cy+100, cx, card_w_bot-60, "系统运行时长", sys_info['uptime']); draw_info_line(cy + 150, cx, card_w_bot - 60, "网络 上传/下载", f"{sys_info['net_sent']} / {sys_info['net_recv']}")
        cx, cy = draw_card((padding_bot*2 + card_w_bot, y_bot), (card_w_bot, card_h_bot), "AstrBot 信息", 'bot', C_TEXT_MAIN); draw_info_line(cy, cx, card_w_bot-60, "Bot运行时长", bot_info['uptime']); draw_info_line(cy+50, cx, card_w_bot-60, "已加载插件数", bot_info['plugins']); draw_info_line(cy+100, cx, card_w_bot-60, "消息平台数", bot_info['platforms']); draw_info_line(cy+150, cx, card_w_bot-60, "消息总数", bot_info['message_count']); draw_info_line(cy+200, cx, card_w_bot-60, "Bot内存占用", bot_info['mem_usage'])

        final_image = Image.alpha_composite(base, canvas)
        img_buffer = io.BytesIO()
        final_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return img_buffer.getvalue()

    @filter.command("sysinfo")
    async def sysinfo(self, event: AstrMessageEvent):
        tmp_file_path = None
        try:
            logger.info("开始生成精美系统状态报告...")
            system_info = self.get_system_info()
            bot_info = self.get_astrbot_info()
            img_data = self.create_system_info_image(system_info, bot_info)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(img_data)
                tmp_file_path = tmp_file.name
            yield event.chain_result([Plain("📊 这是您当前的系统状态面板："), AstrImage.fromFileSystem(tmp_file_path)])
            logger.info("系统信息面板发送成功。")
        except Exception as e:
            logger.error(f"生成或发送系统信息面板时发生错误: {e}", exc_info=True)
            yield event.plain_result(f"❌ 生成报告时发生内部错误，请检查日志。")
        finally:
            if tmp_file_path and os.path.exists(tmp_file_path):
                try: os.unlink(tmp_file_path)
                except Exception as e: logger.warning(f"清理临时文件失败: {e}")

    async def terminate(self):
        logger.info("精美系统信息面板插件已卸载")