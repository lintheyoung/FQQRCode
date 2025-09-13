# server.py - 优化的艺术作品截图系统 (琉璃光影主题)
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn
import asyncio
import uuid
import time
import base64
import os
from typing import Optional
import qrcode
from io import BytesIO

# 环境变量配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
# 动态使用主机和端口生成SERVER_URL，确保在不同环境中都能正常工作
# 在生产环境中，您可能需要手动设置SERVER_URL为一个可公开访问的地址
SERVER_URL = os.getenv("SERVER_URL", f"http://{HOST}:{PORT}") 
if HOST == "0.0.0.0":
    # 如果HOST是0.0.0.0，二维码URL最好使用一个具体的IP地址，如localhost或局域网IP
    # 这里我们默认为localhost，您也可以手动替换为您的局域网IP地址
    try:
        import socket
        # 尝试获取本机局域网IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        SERVER_URL = f"http://{local_ip}:{PORT}"
    except Exception:
        SERVER_URL = f"http://localhost:{PORT}" # 获取失败则回退

app = FastAPI()

# 内存存储（生产环境建议使用Redis）
screenshot_requests = {}
screenshots = {}

class ScreenshotRequest(BaseModel):
    user_id: str

class ScreenshotUpload(BaseModel):
    request_id: str
    image_data: str  # base64编码的图片

# 创建静态文件目录
os.makedirs("static", exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """首页 - 生成二维码 (全新琉璃光影主题)"""
    # 二维码指向的URL（手机扫码后访问的页面）
    qr_url = f"{SERVER_URL}/mobile"
    
    # 生成二维码
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <title>交互艺术截图系统</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400&display=swap');
            
            body, html {{
                margin: 0;
                padding: 0;
                height: 100%;
                font-family: 'Noto Sans SC', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                text-align: center;
                overflow: hidden;
            }}

            .background {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(45deg, #fdeff9, #e8f5ff, #e5fffa, #fff3e6);
                background-size: 400% 400%;
                animation: gradientBG 15s ease infinite;
                z-index: -1;
            }}

            @keyframes gradientBG {{
                0% {{ background-position: 0% 50%; }}
                50% {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}

            .card {{
                background: rgba(255, 255, 255, 0.6);
                padding: 40px;
                border-radius: 25px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.3);
                transition: transform 0.3s ease;
            }}
            
            .card:hover {{
                 transform: translateY(-5px);
            }}

            h1 {{
                font-weight: 400;
                color: #333;
                font-size: 2.2em;
                margin-bottom: 10px;
            }}

            p {{
                color: #555;
                font-size: 1.1em;
                font-weight: 300;
            }}

            .qr-code {{
                margin-top: 25px;
                padding: 10px;
                background: white;
                border-radius: 18px;
                display: inline-block;
                box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            }}

            img {{
                max-width: 250px;
                border-radius: 12px;
                display: block;
            }}
            
            .footer-text {{
                margin-top: 25px;
                font-size: 0.9em;
                color: #777;
            }}
        </style>
    </head>
    <body>
        <div class="background"></div>
        <div class="card">
            <h1>光影捕捉</h1>
            <p>扫描二维码，进入艺术创作空间</p>
            <div class="qr-code">
                <img src="data:image/png;base64,{qr_base64}" alt="二维码" />
            </div>
            <p class="footer-text">实时记录，即刻分享</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/mobile")
async def mobile_page():
    """手机端页面 - 琉璃光影主题"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <title>艺术作品截图</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500&display=swap');

            :root {
                --bg-start: #e0c3fc;
                --bg-end: #8ec5fc;
                --text-primary: #333;
                --text-secondary: #555;
                --accent-color: #89f7fe;
                --accent-color-end: #66a6ff;
                --card-bg: rgba(255, 255, 255, 0.5);
                --card-border: rgba(255, 255, 255, 0.3);
                --success: #28a745;
                --error: #dc3545;
                --warning: #ffc107;
                --info: #17a2b8;
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body, html {
                height: 100%;
                font-family: 'Noto Sans SC', sans-serif;
                color: var(--text-primary);
                overflow-x: hidden;
            }

            body {
                background: linear-gradient(125deg, var(--bg-start) 0%, var(--bg-end) 100%);
                background-attachment: fixed;
            }

            /* 主容器 */
            .container {
                padding: 20px;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 25px;
            }
            
            /* 卡片基类 */
            .card {
                width: 100%;
                max-width: 500px;
                background: var(--card-bg);
                backdrop-filter: blur(15px);
                -webkit-backdrop-filter: blur(15px);
                border-radius: 20px;
                border: 1px solid var(--card-border);
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
                padding: 25px;
                text-align: center;
            }
            
            /* 头部区域 */
            .header .title {
                font-size: 1.8em;
                font-weight: 500;
                margin-bottom: 8px;
            }
            
            .header .subtitle {
                font-size: 0.95em;
                font-weight: 300;
                color: var(--text-secondary);
            }
            
            /* 控制区域 */
            .controls {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 20px;
            }
            
            /* 按钮样式 */
            .capture-btn {
                background-image: linear-gradient(to right, var(--accent-color) 0%, var(--accent-color-end) 51%, var(--accent-color) 100%);
                background-size: 200% auto;
                border: none;
                border-radius: 50px;
                padding: 16px 35px;
                font-size: 1.1em;
                color: white;
                font-weight: 400;
                cursor: pointer;
                transition: all 0.4s ease;
                box-shadow: 0 10px 20px -8px rgba(102, 166, 255, 0.6);
                width: 220px;
            }
            
            .capture-btn:hover {
                background-position: right center;
                transform: translateY(-2px);
                box-shadow: 0 12px 25px -8px rgba(102, 166, 255, 0.8);
            }
            
            .capture-btn:disabled {
                opacity: 0.7;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            /* 加载动画: 三点脉冲 */
            .loading {
                display: none;
                text-align: center;
            }
            .pulsing-dots {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 15px;
                margin-bottom: 15px;
            }
            .pulsing-dots div {
                width: 12px;
                height: 12px;
                background-color: var(--accent-color-end);
                border-radius: 50%;
                animation: pulse 1.4s infinite ease-in-out both;
            }
            .pulsing-dots div:nth-child(1) { animation-delay: -0.32s; }
            .pulsing-dots div:nth-child(2) { animation-delay: -0.16s; }
            
            @keyframes pulse {
              0%, 80%, 100% { transform: scale(0); }
              40% { transform: scale(1.0); }
            }
            
            .loading-text {
                font-size: 1em;
                font-weight: 300;
                color: var(--text-secondary);
            }
            
            /* 状态消息 */
            #status { width: 100%; }
            .status-box {
                padding: 12px 15px;
                border-radius: 12px;
                font-size: 0.9em;
                font-weight: 400;
                border: 1px solid transparent;
            }
            .status-box.success { background-color: rgba(40, 167, 69, 0.1); border-color: rgba(40, 167, 69, 0.2); color: var(--success); }
            .status-box.error   { background-color: rgba(220, 53, 69, 0.1); border-color: rgba(220, 53, 69, 0.2); color: var(--error); }
            .status-box.warning { background-color: rgba(255, 193, 7, 0.1); border-color: rgba(255, 193, 7, 0.2); color: #c89600; }
            .status-box.info    { background-color: rgba(23, 162, 184, 0.1); border-color: rgba(23, 162, 184, 0.2); color: var(--info); }
            
            /* 截图显示区域 */
            .screenshot-container {
                display: none;
                border-radius: 20px;
                overflow: hidden;
                width: 100%;
                max-width: 500px;
            }
            
            .screenshot {
                width: 100%;
                height: auto;
                display: block;
                transition: opacity 0.5s ease, transform 0.5s ease;
                opacity: 0;
                transform: scale(0.95);
            }
            
            .screenshot.show {
                opacity: 1;
                transform: scale(1);
            }
            
            /* 全屏查看 */
            .fullscreen-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                z-index: 1000;
                display: none;
                align-items: center;
                justify-content: center;
                backdrop-filter: blur(5px);
            }
            
            .fullscreen-image {
                max-width: 95vw;
                max-height: 95vh;
                border-radius: 10px;
                box-shadow: 0 0 60px rgba(0,0,0,0.5);
            }
            
            .close-fullscreen {
                position: absolute;
                top: 20px;
                right: 20px;
                background: rgba(255,255,255,0.2);
                border: none;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                color: white;
                font-size: 24px;
                line-height: 40px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .close-fullscreen:hover { background: rgba(255,255,255,0.3); transform: scale(1.1); }

        </style>
    </head>
    <body>
        <div class="container">
            <div class="card header">
                <h1 class="title">光影瞬间</h1>
                <p class="subtitle">捕捉创作过程中的每一个精彩时刻</p>
            </div>
            
            <div class="card controls">
                <button id="captureBtn" class="capture-btn" onclick="requestScreenshot()">
                    📸 捕捉此刻
                </button>
                
                <div id="loading" class="loading">
                    <div class="pulsing-dots"><div></div><div></div><div></div></div>
                    <div class="loading-text">正在连接艺术空间...</div>
                </div>
                
                <div id="status"></div>
            </div>
            
            <div class="screenshot-container card" id="screenshotContainer">
                <img id="screenshot" class="screenshot" onclick="openFullscreen()" />
            </div>
        </div>
        
        <div class="fullscreen-overlay" id="fullscreenOverlay" onclick="closeFullscreen()">
            <img id="fullscreenImage" class="fullscreen-image" />
            <button class="close-fullscreen" onclick="event.stopPropagation(); closeFullscreen();">&times;</button>
        </div>
        
        <script>
            let currentRequestId = null;
            let pollInterval = null;

            // 页面加载完成后自动请求一次
            window.addEventListener('load', () => {
                setTimeout(() => requestScreenshot(true), 500);
            });
            
            async function requestScreenshot(isAuto = false) {
                const captureBtn = document.getElementById('captureBtn');
                const loading = document.getElementById('loading');
                const loadingText = document.querySelector('.loading-text');
                
                captureBtn.disabled = true;
                captureBtn.style.display = 'none';
                loading.style.display = 'block';
                
                if (isAuto) {
                    loadingText.textContent = '正在自动连接艺术空间...';
                    updateStatus('🎨 自动捕捉已启动，请稍候...', 'info');
                } else {
                    loadingText.textContent = '正在捕捉艺术瞬间...';
                    updateStatus('📸 手动捕捉请求已发送...', 'info');
                }
                
                try {
                    const response = await fetch('/api/request-screenshot', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: 'art_viewer_' + Date.now() })
                    });
                    
                    if (!response.ok) throw new Error('网络请求失败');
                    
                    const data = await response.json();
                    currentRequestId = data.request_id;
                    
                    updateStatus('⚡ 正在等待创作设备响应...', 'warning');
                    
                    if (pollInterval) clearInterval(pollInterval);
                    pollInterval = setInterval(checkScreenshot, 1500); // 轮询频率1.5秒
                    
                    // 30秒超时处理
                    setTimeout(() => {
                        if (pollInterval && currentRequestId === data.request_id) {
                            clearInterval(pollInterval);
                            resetUI();
                            updateStatus('⏰ 请求超时，请检查创作设备或重试。', 'error');
                        }
                    }, 30000);
                    
                } catch (error) {
                    resetUI();
                    updateStatus('❌ 连接失败: ' + error.message, 'error');
                    console.error('请求截图失败:', error);
                }
            }
            
            async function checkScreenshot() {
                if (!currentRequestId) return;
                
                try {
                    const response = await fetch(`/api/get-screenshot/${currentRequestId}`);
                    if (!response.ok) return; // 忽略失败的轮询
                    
                    const data = await response.json();
                    
                    if (data.status === 'completed') {
                        clearInterval(pollInterval);
                        
                        const screenshot = document.getElementById('screenshot');
                        const screenshotContainer = document.getElementById('screenshotContainer');
                        
                        screenshot.src = 'data:image/png;base64,' + data.image_data;
                        screenshotContainer.style.display = 'block';
                        screenshot.classList.add('show');
                        
                        resetUI();
                        updateStatus('✨ 艺术瞬间捕捉成功！', 'success');
                        
                        setTimeout(() => {
                           screenshotContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }, 100);
                        
                        currentRequestId = null;
                        
                        setTimeout(() => {
                            updateStatus('🎭 可再次点击按钮，捕捉新的创作。', 'info');
                        }, 5000);

                    } else if (data.status === 'processing') {
                        updateStatus('🎨 创作设备正在处理，即将完成...', 'warning');
                    }
                } catch (error) {
                    console.error('轮询错误:', error);
                }
            }
            
            function updateStatus(message, type) {
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = `<div class="status-box ${type}">${message}</div>`;
            }

            function resetUI() {
                const captureBtn = document.getElementById('captureBtn');
                const loading = document.getElementById('loading');
                captureBtn.disabled = false;
                captureBtn.style.display = 'block';
                loading.style.display = 'none';
            }
            
            // 全屏查看功能
            function openFullscreen() {
                const screenshot = document.getElementById('screenshot');
                const fullscreenOverlay = document.getElementById('fullscreenOverlay');
                const fullscreenImage = document.getElementById('fullscreenImage');
                
                if (screenshot.src) {
                    fullscreenImage.src = screenshot.src;
                    fullscreenOverlay.style.display = 'flex';
                    document.body.style.overflow = 'hidden';
                }
            }
            
            function closeFullscreen() {
                const fullscreenOverlay = document.getElementById('fullscreenOverlay');
                fullscreenOverlay.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
            
            // 页面隐藏或卸载时清理定时器
            document.addEventListener('visibilitychange', () => {
                if (document.hidden && pollInterval) clearInterval(pollInterval);
            });
            window.addEventListener('beforeunload', () => {
                if (pollInterval) clearInterval(pollInterval);
            });

        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# =======================================================
# 以下为后端API和服务逻辑，与原始代码完全一致，未做任何修改
# =======================================================

# ==================== 新增修改 ====================
# 添加一个路由来提供根目录下的验证文件
@app.get("/60d1dbab8d131699df1df834e9fc0fd8.txt", response_class=FileResponse)
async def get_verification_file():
    """提供根目录下的验证文件"""
    # 从 static 目录中返回该文件
    file_path = "static/60d1dbab8d131699df1df834e9fc0fd8.txt"
    if os.path.exists(file_path):
        return FileResponse(path=file_path, media_type='text/plain')
    raise HTTPException(status_code=404, detail="File not found")
# ================================================

@app.post("/api/request-screenshot")
async def request_screenshot_api(request: ScreenshotRequest): # Renamed to avoid conflict
    """接收截图请求"""
    request_id = str(uuid.uuid4())
    screenshot_requests[request_id] = {
        "user_id": request.user_id,
        "timestamp": time.time(),
        "status": "pending"
    }
    return {"request_id": request_id, "status": "created"}

@app.get("/api/check-requests")
async def check_requests():
    """电脑端轮询检查是否有新的截图请求"""
    pending_requests = [
        {"request_id": req_id, **req_data} 
        for req_id, req_data in screenshot_requests.items() 
        if req_data["status"] == "pending"
    ]
    
    if pending_requests:
        # 标记为处理中
        for req in pending_requests:
            screenshot_requests[req["request_id"]]["status"] = "processing"
        
        return {"has_requests": True, "requests": pending_requests}
    
    return {"has_requests": False, "requests": []}

@app.post("/api/upload-screenshot")
async def upload_screenshot(upload: ScreenshotUpload):
    """接收电脑端上传的截图"""
    if upload.request_id not in screenshot_requests:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # 保存截图
    screenshots[upload.request_id] = {
        "image_data": upload.image_data,
        "timestamp": time.time()
    }
    
    # 更新请求状态
    screenshot_requests[upload.request_id]["status"] = "completed"
    
    return {"status": "uploaded"}

@app.get("/api/get-screenshot/{request_id}")
async def get_screenshot(request_id: str):
    """获取截图结果"""
    if request_id not in screenshot_requests:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request_data = screenshot_requests[request_id]
    
    if request_data["status"] == "completed" and request_id in screenshots:
        return {
            "status": "completed",
            "image_data": screenshots[request_id]["image_data"]
        }
    elif request_data["status"] == "processing":
        return {"status": "processing"}
    else:
        return {"status": "pending"}

# 清理过期请求（可选的后台任务）
async def cleanup_expired_requests():
    """清理超过1小时的请求"""
    while True:
        await asyncio.sleep(300)  # 每5分钟检查一次
        current_time = time.time()
        expired_requests = [
            req_id for req_id, req_data in list(screenshot_requests.items())
            if current_time - req_data.get("timestamp", 0) > 3600  # 1小时
        ]
        
        for req_id in expired_requests:
            screenshot_requests.pop(req_id, None)
            screenshots.pop(req_id, None)

@app.on_event("startup")
async def startup_event():
    # 启动清理任务
    asyncio.create_task(cleanup_expired_requests())

if __name__ == "__main__":
    print("艺术作品截图系统启动中...")
    print(f"请用PC浏览器访问: http://localhost:{PORT} 或 http://{HOST}:{PORT}")
    print(f"手机扫码将访问: {SERVER_URL}/mobile")
    # uvicorn.run("server:app", host=HOST, port=PORT, reload=True) # for file name server.py
    uvicorn.run(app, host=HOST, port=PORT)