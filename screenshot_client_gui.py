# screenshot_client_gui.py
import customtkinter as ctk
import requests
import time
import base64
import io
import json
from PIL import ImageGrab, Image, ImageTk
import logging
from typing import List, Dict, Any, Optional, Tuple
import sys
import threading
import queue
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import platform

# Windows 高 DPI 支持
if platform.system() == 'Windows':
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

# 配置 CustomTkinter
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('screenshot_client.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ScreenshotClient:
    def __init__(self, server_url: str = "http://localhost:8000", capture_region: Optional[Tuple[int, int, int, int]] = None):
        """
        初始化截图客户端
        
        Args:
            server_url: 服务器地址，例如 "http://192.168.1.100:8000"
            capture_region: 截图区域 (x, y, width, height)，None表示全屏截图
        """
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 10
        self.running = False
        self.capture_region = capture_region
        
        logger.info(f"截图客户端初始化完成，服务器地址: {self.server_url}")
        if self.capture_region:
            logger.info(f"截图区域: x={self.capture_region[0]}, y={self.capture_region[1]}, "
                       f"width={self.capture_region[2]}, height={self.capture_region[3]}")
        else:
            logger.info("截图模式: 全屏截图")
    
    def take_screenshot(self) -> str:
        """
        截取屏幕并返回base64编码的图片数据
        
        Returns:
            base64编码的PNG图片字符串
        """
        try:
            if self.capture_region:
                # 指定区域截图
                x, y, width, height = self.capture_region
                bbox = (x, y, x + width, y + height)
                logger.info(f"准备区域截图，bbox: {bbox}")
                screenshot = ImageGrab.grab(bbox=bbox)
                logger.info(f"区域截图成功，实际尺寸: {screenshot.size}")
            else:
                # 全屏截图
                logger.info("准备全屏截图")
                screenshot = ImageGrab.grab()
                logger.info(f"全屏截图成功，屏幕尺寸: {screenshot.size}")
            
            # 转换为字节流
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            buffer.seek(0)
            
            # 编码为base64
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info(f"截图编码完成，图片大小: {len(image_data)} 字符")
            return image_data
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise
    
    def check_requests(self) -> List[Dict[str, Any]]:
        """
        检查服务器是否有新的截图请求
        
        Returns:
            待处理的请求列表
        """
        try:
            response = self.session.get(f"{self.server_url}/api/check-requests")
            response.raise_for_status()
            
            data = response.json()
            if data.get("has_requests", False):
                requests_list = data.get("requests", [])
                logger.info(f"发现 {len(requests_list)} 个待处理的截图请求")
                return requests_list
            
            return []
            
        except requests.RequestException as e:
            logger.error(f"检查请求失败: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"解析服务器响应失败: {e}")
            return []
    
    def upload_screenshot(self, request_id: str, image_data: str) -> bool:
        """
        上传截图到服务器
        
        Args:
            request_id: 请求ID
            image_data: base64编码的图片数据
            
        Returns:
            是否上传成功
        """
        try:
            payload = {
                "request_id": request_id,
                "image_data": image_data
            }
            
            response = self.session.post(
                f"{self.server_url}/api/upload-screenshot",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"截图上传成功，请求ID: {request_id}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"上传截图失败: {e}")
            return False
        except Exception as e:
            logger.error(f"上传截图时发生未知错误: {e}")
            return False
    
    def process_screenshot_request(self, request: Dict[str, Any]) -> bool:
        """
        处理单个截图请求
        
        Args:
            request: 截图请求信息
            
        Returns:
            是否处理成功
        """
        request_id = request.get("request_id")
        user_id = request.get("user_id")
        
        logger.info(f"开始处理截图请求 - ID: {request_id}, 用户: {user_id}")
        
        try:
            # 截图
            image_data = self.take_screenshot()
            
            # 上传截图
            success = self.upload_screenshot(request_id, image_data)
            
            if success:
                logger.info(f"截图请求处理完成 - ID: {request_id}")
            else:
                logger.error(f"截图请求处理失败 - ID: {request_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"处理截图请求时发生错误 - ID: {request_id}, 错误: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        测试与服务器的连接
        
        Returns:
            连接是否正常
        """
        try:
            response = self.session.get(f"{self.server_url}/api/check-requests")
            response.raise_for_status()
            logger.info("服务器连接测试成功")
            return True
        except Exception as e:
            logger.error(f"服务器连接测试失败: {e}")
            return False
    
    def run(self, poll_interval: float = 2.0, log_callback=None):
        """
        启动客户端主循环
        
        Args:
            poll_interval: 轮询间隔（秒）
            log_callback: 日志回调函数
        """
        logger.info("截图客户端启动中...")
        
        # 测试连接
        if not self.test_connection():
            logger.error("无法连接到服务器，请检查服务器地址和网络连接")
            return
        
        self.running = True
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        logger.info(f"开始轮询服务器，间隔: {poll_interval} 秒")
        
        try:
            while self.running:
                try:
                    # 检查是否有新请求
                    requests_list = self.check_requests()
                    
                    # 处理所有待处理的请求
                    for request in requests_list:
                        if not self.running:
                            break
                        self.process_screenshot_request(request)
                    
                    # 重置错误计数
                    consecutive_errors = 0
                    
                    # 等待下次轮询
                    time.sleep(poll_interval)
                    
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"轮询循环中发生错误 ({consecutive_errors}/{max_consecutive_errors}): {e}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("连续错误次数过多，停止客户端")
                        break
                    
                    # 等待更长时间后重试
                    time.sleep(poll_interval * 2)
        
        finally:
            self.running = False
            logger.info("截图客户端已停止")
    
    def stop(self):
        """停止客户端"""
        self.running = False
    
    def set_capture_region(self, region: Optional[Tuple[int, int, int, int]]):
        """
        设置截图区域
        
        Args:
            region: (x, y, width, height) 或 None (全屏)
        """
        self.capture_region = region
        if region:
            logger.info(f"截图区域已设置为: x={region[0]}, y={region[1]}, width={region[2]}, height={region[3]}")
        else:
            logger.info("截图区域已设置为: 全屏")

class RegionSelector:
    """截图区域选择器"""
    
    def __init__(self):
        self.region = None
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.selecting = False
        
    def select_region_gui(self) -> Optional[Tuple[int, int, int, int]]:
        """
        使用图形界面选择截图区域
        
        Returns:
            (x, y, width, height) 或 None
        """
        try:
            # 创建全屏窗口
            root = tk.Tk()
            
            # 获取屏幕尺寸
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            # 设置窗口属性
            root.attributes('-fullscreen', True)
            root.attributes('-topmost', True)
            root.configure(cursor='crosshair')
            root.configure(bg='black')
            root.attributes('-alpha', 0.3)  # 半透明
            
            # 确保窗口覆盖整个屏幕
            root.geometry(f"{screen_width}x{screen_height}+0+0")
            
            # 创建画布，明确指定大小
            canvas = tk.Canvas(root, highlightthickness=0, width=screen_width, height=screen_height)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # 选择状态
            selection_rect = None
            
            def on_button_press(event):
                nonlocal selection_rect
                self.start_x = event.x
                self.start_y = event.y
                self.selecting = True
                if selection_rect:
                    canvas.delete(selection_rect)
            
            def on_mouse_drag(event):
                nonlocal selection_rect
                if self.selecting:
                    if selection_rect:
                        canvas.delete(selection_rect)
                    self.end_x = event.x
                    self.end_y = event.y
                    selection_rect = canvas.create_rectangle(
                        self.start_x, self.start_y, self.end_x, self.end_y,
                        outline='red', width=2
                    )
            
            def on_button_release(event):
                nonlocal selection_rect
                self.selecting = False
                self.end_x = event.x
                self.end_y = event.y
                
                # 计算区域
                x = min(self.start_x, self.end_x)
                y = min(self.start_y, self.end_y)
                width = abs(self.end_x - self.start_x)
                height = abs(self.end_y - self.start_y)
                
                if width > 10 and height > 10:  # 最小区域限制
                    self.region = (x, y, width, height)
                    root.quit()
                else:
                    if selection_rect:
                        canvas.delete(selection_rect)
                    selection_rect = None
            
            def on_escape(event):
                self.region = None
                root.quit()
            
            # 绑定事件
            canvas.bind('<Button-1>', on_button_press)
            canvas.bind('<B1-Motion>', on_mouse_drag)
            canvas.bind('<ButtonRelease-1>', on_button_release)
            root.bind('<Escape>', on_escape)
            
            # 显示说明
            info_label = tk.Label(root, text="拖拽鼠标选择截图区域，按ESC取消", 
                                 fg='white', bg='black', font=('Arial', 12))
            info_label.pack(pady=10)
            
            # 显示屏幕信息
            screen_info_label = tk.Label(root, text=f"屏幕大小: {screen_width}x{screen_height}", 
                                        fg='white', bg='black', font=('Arial', 10))
            screen_info_label.pack(pady=5)
            
            # 强制更新窗口，确保正确显示
            root.update_idletasks()
            root.update()
            
            root.mainloop()
            root.destroy()
            
            return self.region
            
        except Exception as e:
            logger.error(f"GUI区域选择失败: {e}")
            return None

class LogHandler(logging.Handler):
    """自定义日志处理器，用于将日志发送到GUI"""
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        
    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)

class ScreenshotClientGUI:
    """截图客户端GUI主窗口"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("远程截图客户端")
        self.root.geometry("900x650")
        
        # 客户端实例
        self.client = None
        self.client_thread = None
        self.running = False
        
        # 日志队列（线程安全）
        self.log_queue = queue.Queue()
        
        # 设置自定义日志处理器
        self.log_handler = LogHandler(self.log_queue)
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(self.log_handler)
        
        # 配置变量
        self.server_url = tk.StringVar(value="http://localhost:8000")
        self.poll_interval = tk.DoubleVar(value=2.0)
        self.capture_region = None
        
        # 显示屏幕信息
        self.screen_info = self.get_screen_info()
        
        self.setup_ui()
        
        # 定期更新日志显示
        self.update_logs()
        
    def get_screen_info(self):
        """获取屏幕信息"""
        temp_root = tk.Tk()
        temp_root.withdraw()
        info = {
            "width": temp_root.winfo_screenwidth(),
            "height": temp_root.winfo_screenheight()
        }
        temp_root.destroy()
        return info
        
    def setup_ui(self):
        """设置UI界面"""
        # 主容器
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 配置区域
        config_frame = ctk.CTkFrame(main_container)
        config_frame.pack(fill="x", padx=5, pady=5)
        
        # 服务器地址
        server_frame = ctk.CTkFrame(config_frame)
        server_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(server_frame, text="服务器地址:", width=100).pack(side="left", padx=5)
        ctk.CTkEntry(server_frame, textvariable=self.server_url, width=300).pack(side="left", padx=5)
        
        # 轮询间隔
        interval_frame = ctk.CTkFrame(config_frame)
        interval_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(interval_frame, text="轮询间隔(秒):", width=100).pack(side="left", padx=5)
        ctk.CTkEntry(interval_frame, textvariable=self.poll_interval, width=100).pack(side="left", padx=5)
        
        # 截图区域设置
        region_frame = ctk.CTkFrame(config_frame)
        region_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(region_frame, text="截图区域:", width=100).pack(side="left", padx=5)
        self.region_label = ctk.CTkLabel(region_frame, text="全屏", width=200)
        self.region_label.pack(side="left", padx=5)
        
        region_btn_frame = ctk.CTkFrame(region_frame)
        region_btn_frame.pack(side="left", padx=5)
        
        ctk.CTkButton(region_btn_frame, text="选择区域", command=self.select_region, width=100).pack(side="left", padx=2)
        ctk.CTkButton(region_btn_frame, text="手动输入", command=self.manual_input_region, width=100).pack(side="left", padx=2)
        ctk.CTkButton(region_btn_frame, text="常用预设", command=self.show_presets, width=100).pack(side="left", padx=2)
        ctk.CTkButton(region_btn_frame, text="全屏", command=self.set_fullscreen, width=100).pack(side="left", padx=2)
        
        # 控制按钮
        control_frame = ctk.CTkFrame(main_container)
        control_frame.pack(fill="x", padx=5, pady=10)
        
        self.start_btn = ctk.CTkButton(control_frame, text="启动客户端", command=self.start_client, width=150)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(control_frame, text="停止客户端", command=self.stop_client, width=150, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        ctk.CTkButton(control_frame, text="测试连接", command=self.test_connection, width=150).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="测试截图", command=self.test_screenshot, width=150).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="清空日志", command=self.clear_logs, width=150).pack(side="left", padx=5)
        
        # 状态显示
        status_frame = ctk.CTkFrame(main_container)
        status_frame.pack(fill="x", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(status_frame, text="状态: 未运行", text_color="orange")
        self.status_label.pack(side="left", padx=5)
        
        # 显示屏幕信息
        screen_label = ctk.CTkLabel(status_frame, text=f"屏幕分辨率: {self.screen_info['width']}x{self.screen_info['height']}")
        screen_label.pack(side="right", padx=5)
        
        # 日志显示区域
        log_frame = ctk.CTkFrame(main_container)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(log_frame, text="运行日志:").pack(anchor="w", padx=5, pady=2)
        
        # 日志文本框
        self.log_text = ctk.CTkTextbox(log_frame, height=300)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
    def select_region(self):
        """选择截图区域"""
        # 最小化主窗口
        self.root.withdraw()
        
        # 等待一下让窗口完全隐藏
        time.sleep(0.5)
        
        # 强制更新确保窗口状态
        self.root.update()
        
        # 选择区域
        selector = RegionSelector()
        region = selector.select_region_gui()
        
        # 恢复主窗口
        self.root.deiconify()
        
        if region:
            self.capture_region = region
            self.region_label.configure(text=f"区域: {region[0]}, {region[1]}, {region[2]}x{region[3]}")
            self.log_info(f"已选择截图区域: x={region[0]}, y={region[1]}, width={region[2]}, height={region[3]}")
        else:
            self.log_info("取消区域选择")
            
    def set_fullscreen(self):
        """设置全屏截图"""
        self.capture_region = None
        self.region_label.configure(text="全屏")
        self.log_info("已设置为全屏截图模式")
        
    def manual_input_region(self):
        """手动输入截图区域"""
        # 创建输入对话框
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("手动输入截图区域")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 显示屏幕信息
        info_text = f"当前屏幕分辨率: {self.screen_info['width']}x{self.screen_info['height']}"
        ctk.CTkLabel(dialog, text=info_text, text_color="gray").pack(pady=5)
        
        # 输入框
        ctk.CTkLabel(dialog, text="请输入截图区域坐标（像素）：").pack(pady=10)
        
        # 坐标输入
        input_frame = ctk.CTkFrame(dialog)
        input_frame.pack(pady=10)
        
        entries = {}
        for label, key in [("X坐标:", "x"), ("Y坐标:", "y"), ("宽度:", "width"), ("高度:", "height")]:
            frame = ctk.CTkFrame(input_frame)
            frame.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(frame, text=label, width=80).pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame, width=150)
            entry.pack(side="left", padx=5)
            entries[key] = entry
            
        # 如果已有区域设置，填充当前值
        if self.capture_region:
            entries["x"].insert(0, str(self.capture_region[0]))
            entries["y"].insert(0, str(self.capture_region[1]))
            entries["width"].insert(0, str(self.capture_region[2]))
            entries["height"].insert(0, str(self.capture_region[3]))
        
        result = {"confirmed": False}
        
        def confirm():
            try:
                x = int(entries["x"].get())
                y = int(entries["y"].get())
                width = int(entries["width"].get())
                height = int(entries["height"].get())
                
                if width > 0 and height > 0:
                    self.capture_region = (x, y, width, height)
                    self.region_label.configure(text=f"区域: {x}, {y}, {width}x{height}")
                    self.log_info(f"已手动设置截图区域: x={x}, y={y}, width={width}, height={height}")
                    result["confirmed"] = True
                    dialog.destroy()
                else:
                    messagebox.showerror("错误", "宽度和高度必须大于0")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
        
        def cancel():
            dialog.destroy()
        
        # 按钮
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="确定", command=confirm, width=100).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="取消", command=cancel, width=100).pack(side="left", padx=5)
        
    def show_presets(self):
        """显示常用预设区域"""
        # 创建预设对话框
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("常用预设区域")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 预设列表
        ctk.CTkLabel(dialog, text=f"当前屏幕: {self.screen_info['width']}x{self.screen_info['height']}").pack(pady=10)
        
        # 根据当前屏幕尺寸生成预设
        width = self.screen_info['width']
        height = self.screen_info['height']
        
        presets = [
            ("左半屏", (0, 0, width // 2, height)),
            ("右半屏", (width // 2, 0, width // 2, height)),
            ("上半屏", (0, 0, width, height // 2)),
            ("下半屏", (0, height // 2, width, height // 2)),
            ("中央区域 (1/2)", (width // 4, height // 4, width // 2, height // 2)),
            ("中央区域 (2/3)", (width // 6, height // 6, width * 2 // 3, height * 2 // 3)),
            ("左上角 (1/4)", (0, 0, width // 2, height // 2)),
            ("右上角 (1/4)", (width // 2, 0, width // 2, height // 2)),
            ("左下角 (1/4)", (0, height // 2, width // 2, height // 2)),
            ("右下角 (1/4)", (width // 2, height // 2, width // 2, height // 2)),
        ]
        
        # 创建滚动框架
        scroll_frame = ctk.CTkScrollableFrame(dialog, height=300)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        def select_preset(region):
            self.capture_region = region
            self.region_label.configure(text=f"区域: {region[0]}, {region[1]}, {region[2]}x{region[3]}")
            self.log_info(f"已选择预设区域: x={region[0]}, y={region[1]}, width={region[2]}, height={region[3]}")
            dialog.destroy()
        
        # 显示预设选项
        for name, region in presets:
            frame = ctk.CTkFrame(scroll_frame)
            frame.pack(fill="x", padx=5, pady=2)
            
            text = f"{name}: 位置({region[0]}, {region[1]}) 大小({region[2]}x{region[3]})"
            ctk.CTkLabel(frame, text=text, width=350).pack(side="left", padx=5)
            ctk.CTkButton(frame, text="选择", command=lambda r=region: select_preset(r), width=80).pack(side="right", padx=5)
        
        # 关闭按钮
        ctk.CTkButton(dialog, text="关闭", command=dialog.destroy, width=100).pack(pady=10)
        
    def test_connection(self):
        """测试连接"""
        def test():
            try:
                client = ScreenshotClient(self.server_url.get())
                if client.test_connection():
                    self.log_info("服务器连接测试成功")
                    self.root.after(0, lambda: messagebox.showinfo("连接测试", "服务器连接成功！"))
                else:
                    self.log_error("服务器连接测试失败")
                    self.root.after(0, lambda: messagebox.showerror("连接测试", "服务器连接失败！"))
            except Exception as e:
                self.log_error(f"连接测试出错: {e}")
                self.root.after(0, lambda: messagebox.showerror("连接测试", f"连接测试出错: {e}"))
                
        threading.Thread(target=test, daemon=True).start()
        
    def test_screenshot(self):
        """测试截图功能"""
        def test():
            try:
                self.log_info("开始测试截图...")
                
                # 创建临时客户端
                client = ScreenshotClient("http://localhost:8000", self.capture_region)
                
                # 执行截图
                image_data = client.take_screenshot()
                
                # 解码并显示预览
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                
                # 获取图片信息
                width, height = image.size
                self.log_info(f"截图成功！尺寸: {width}x{height}")
                
                # 在新窗口显示预览
                self.root.after(0, lambda: self.show_screenshot_preview(image))
                
            except Exception as e:
                self.log_error(f"截图测试失败: {e}")
                self.root.after(0, lambda: messagebox.showerror("截图测试", f"截图测试失败: {e}"))
                
        threading.Thread(target=test, daemon=True).start()
        
    def show_screenshot_preview(self, image):
        """显示截图预览"""
        preview = ctk.CTkToplevel(self.root)
        preview.title("截图预览")
        preview.transient(self.root)
        
        # 缩放图片以适应窗口
        max_size = (800, 600)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 转换为 PhotoImage
        photo = ImageTk.PhotoImage(image)
        
        # 显示图片
        label = ctk.CTkLabel(preview, image=photo, text="")
        label.image = photo  # 保持引用
        label.pack(padx=10, pady=10)
        
        # 显示信息
        info_text = f"原始尺寸: {image.width}x{image.height}"
        if self.capture_region:
            info_text += f"\n截图区域: {self.capture_region}"
        else:
            info_text += "\n截图模式: 全屏"
            
        ctk.CTkLabel(preview, text=info_text).pack(pady=5)
        
        # 关闭按钮
        ctk.CTkButton(preview, text="关闭", command=preview.destroy).pack(pady=10)
        
    def start_client(self):
        """启动客户端"""
        if self.running:
            return
            
        # 创建客户端实例
        self.client = ScreenshotClient(self.server_url.get(), self.capture_region)
        
        # 在新线程中运行客户端
        self.client_thread = threading.Thread(
            target=self.client.run,
            args=(self.poll_interval.get(),),
            daemon=True
        )
        
        self.running = True
        self.client_thread.start()
        
        # 更新UI状态
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="状态: 运行中", text_color="green")
        
        self.log_info("客户端已启动")
        
    def stop_client(self):
        """停止客户端"""
        if not self.running:
            return
            
        if self.client:
            self.client.stop()
            
        self.running = False
        
        # 等待线程结束
        if self.client_thread:
            self.client_thread.join(timeout=3)
            
        # 更新UI状态
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="状态: 未运行", text_color="orange")
        
        self.log_info("客户端已停止")
        
    def clear_logs(self):
        """清空日志"""
        self.log_text.delete("1.0", "end")
        
    def log_info(self, message):
        """记录信息日志"""
        logger.info(message)
        
    def log_error(self, message):
        """记录错误日志"""
        logger.error(message)
        
    def update_logs(self):
        """更新日志显示（线程安全）"""
        try:
            while True:
                # 非阻塞获取日志
                log_entry = self.log_queue.get_nowait()
                
                # 在主线程中更新UI
                self.log_text.insert("end", log_entry + "\n")
                self.log_text.see("end")  # 自动滚动到底部
                
                # 限制日志行数
                lines = self.log_text.get("1.0", "end").count('\n')
                if lines > 500:
                    self.log_text.delete("1.0", "2.0")
                    
        except queue.Empty:
            pass
            
        # 定期调用自己
        self.root.after(100, self.update_logs)
        
    def run(self):
        """运行GUI"""
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动主循环
        self.root.mainloop()
        
    def on_closing(self):
        """窗口关闭事件"""
        if self.running:
            if messagebox.askokcancel("退出", "客户端正在运行，确定要退出吗？"):
                self.stop_client()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """主函数"""
    app = ScreenshotClientGUI()
    app.run()

if __name__ == "__main__":
    main()