# screenshot_client.py
import requests
import time
import base64
import io
import json
from PIL import ImageGrab
import logging
from typing import List, Dict, Any, Optional, Tuple
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading

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
                screenshot = ImageGrab.grab(bbox=bbox)
                logger.info(f"区域截图成功，区域: ({x}, {y}, {width}, {height})")
            else:
                # 全屏截图
                screenshot = ImageGrab.grab()
                logger.info("全屏截图成功")
            
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
    
    def run(self, poll_interval: float = 2.0):
        """
        启动客户端主循环
        
        Args:
            poll_interval: 轮询间隔（秒）
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
        logger.info("按 Ctrl+C 停止客户端")
        
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
                    
                except KeyboardInterrupt:
                    logger.info("接收到停止信号")
                    break
                    
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
            import tkinter as tk
            from tkinter import messagebox
            
            # 先全屏截图作为背景
            screenshot = ImageGrab.grab()
            
            # 创建全屏窗口
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            root.attributes('-topmost', True)
            root.configure(cursor='crosshair')
            root.configure(bg='black')
            root.attributes('-alpha', 0.3)  # 半透明
            
            # 创建画布
            canvas = tk.Canvas(root, highlightthickness=0)
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
            
            root.mainloop()
            root.destroy()
            
            return self.region
            
        except ImportError:
            logger.error("无法导入tkinter，请使用命令行方式指定区域")
            return None
        except Exception as e:
            logger.error(f"GUI区域选择失败: {e}")
            return None
    
    def select_region_input(self) -> Optional[Tuple[int, int, int, int]]:
        """
        通过命令行输入选择截图区域
        
        Returns:
            (x, y, width, height) 或 None
        """
        try:
            print("\n=== 设置截图区域 ===")
            print("请输入截图区域坐标（像素）:")
            print("提示：可以使用截图工具或系统信息查看坐标")
            
            x = int(input("起始X坐标: "))
            y = int(input("起始Y坐标: "))
            width = int(input("宽度: "))
            height = int(input("高度: "))
            
            if width > 0 and height > 0:
                return (x, y, width, height)
            else:
                print("宽度和高度必须大于0")
                return None
                
        except ValueError:
            print("输入格式错误，请输入数字")
            return None
        except KeyboardInterrupt:
            return None

def get_capture_region() -> Optional[Tuple[int, int, int, int]]:
    """
    获取截图区域配置
    
    Returns:
        (x, y, width, height) 或 None (全屏)
    """
    print("\n=== 截图区域设置 ===")
    print("1. 全屏截图")
    print("2. 图形界面选择区域 (推荐)")
    print("3. 手动输入坐标")
    print("4. 常用区域预设")
    
    try:
        choice = input("请选择模式 (1-4, 默认1): ").strip()
        
        if choice == "2":
            print("即将打开区域选择界面...")
            time.sleep(1)
            selector = RegionSelector()
            region = selector.select_region_gui()
            if region:
                print(f"已选择区域: x={region[0]}, y={region[1]}, width={region[2]}, height={region[3]}")
                return region
            else:
                print("未选择区域，使用全屏截图")
                return None
                
        elif choice == "3":
            selector = RegionSelector()
            return selector.select_region_input()
            
        elif choice == "4":
            print("\n常用区域预设:")
            print("1. 1920x1080 左半屏 (0, 0, 960, 1080)")
            print("2. 1920x1080 右半屏 (960, 0, 960, 1080)")
            print("3. 1920x1080 上半屏 (0, 0, 1920, 540)")
            print("4. 1920x1080 下半屏 (0, 540, 1920, 540)")
            print("5. 1920x1080 中央区域 (480, 270, 960, 540)")
            
            preset = input("选择预设 (1-5): ").strip()
            presets = {
                "1": (0, 0, 960, 1080),
                "2": (960, 0, 960, 1080),
                "3": (0, 0, 1920, 540),
                "4": (0, 540, 1920, 540),
                "5": (480, 270, 960, 540)
            }
            
            if preset in presets:
                region = presets[preset]
                print(f"已选择预设区域: x={region[0]}, y={region[1]}, width={region[2]}, height={region[3]}")
                return region
        
        # 默认全屏
        print("使用全屏截图模式")
        return None
        
    except KeyboardInterrupt:
        print("\n操作已取消，使用全屏截图")
        return None

def main():
    """主函数"""
    print("=== 远程截图客户端 ===")
    print("请确保服务器已启动并且网络连通")
    print()
    
    # 截图区域配置
    capture_region = get_capture_region()
    
    # 服务器地址配置
    server_url = input("\n请输入服务器地址 (默认: http://localhost:8000): ").strip()
    if not server_url:
        server_url = "http://localhost:8000"
    
    # 轮询间隔配置
    try:
        poll_interval = float(input("请输入轮询间隔秒数 (默认: 2): ") or "2")
    except ValueError:
        poll_interval = 2.0
    
    print(f"\n=== 配置信息 ===")
    print(f"服务器地址: {server_url}")
    print(f"轮询间隔: {poll_interval} 秒")
    if capture_region:
        print(f"截图区域: x={capture_region[0]}, y={capture_region[1]}, width={capture_region[2]}, height={capture_region[3]}")
    else:
        print("截图模式: 全屏截图")
    
    print("\n正在启动客户端...")
    
    # 创建并启动客户端
    client = ScreenshotClient(server_url, capture_region)
    
    try:
        client.run(poll_interval)
    except KeyboardInterrupt:
        logger.info("用户手动停止客户端")
    except Exception as e:
        logger.error(f"客户端运行时发生未知错误: {e}")
    finally:
        client.stop()
        print("\n客户端已停止")

if __name__ == "__main__":
    main()