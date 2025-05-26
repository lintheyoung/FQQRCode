# server.py - 优化的艺术作品截图系统
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
SERVER_URL = os.getenv("SERVER_URL", f"http://localhost:7979")  # 默认使用7979端口

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
    """首页 - 生成二维码"""
    # 二维码指向的URL（手机扫码后访问的页面）
    qr_url = f"{SERVER_URL}/mobile"
    
    # 生成二维码
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>交互艺术截图系统</title>
        <meta charset="utf-8">
        <style>
            body {{ 
                font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; 
                text-align: center; 
                padding: 50px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }}
            .qr-container {{ 
                background: rgba(255,255,255,0.95); 
                border-radius: 20px; 
                padding: 40px; 
                backdrop-filter: blur(10px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #333; font-weight: 300; font-size: 2.5em; margin-bottom: 10px; }}
            p {{ color: #666; font-size: 1.2em; }}
            img {{ max-width: 250px; border-radius: 15px; }}
        </style>
    </head>
    <body>
        <div class="qr-container">
            <h1>交互艺术截图</h1>
            <p>扫描二维码捕捉艺术瞬间</p>
            <img src="data:image/png;base64,{qr_base64}" alt="二维码" />
            <p style="font-size: 0.9em; margin-top: 20px;">实时记录创作过程</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/mobile")
async def mobile_page():
    """手机端页面 - 艺术化设计"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>艺术作品截图</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body { 
                font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; 
                background: #000;
                color: #fff;
                overflow-x: hidden;
                min-height: 100vh;
                position: relative;
            }
            
            /* 动态背景 */
            .bg-animation {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(45deg, #1a1a2e, #16213e, #0f3460);
                background-size: 400% 400%;
                animation: gradientFlow 15s ease infinite;
                z-index: -2;
            }
            
            @keyframes gradientFlow {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            
            /* 浮动粒子效果 */
            .particles {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: -1;
                overflow: hidden;
            }
            
            .particle {
                position: absolute;
                background: rgba(255,255,255,0.1);
                border-radius: 50%;
                animation: float 20s infinite linear;
            }
            
            @keyframes float {
                0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
                10% { opacity: 1; }
                90% { opacity: 1; }
                100% { transform: translateY(-100px) rotate(360deg); opacity: 0; }
            }
            
            /* 主容器 */
            .container {
                position: relative;
                z-index: 10;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }
            
            /* 头部区域 */
            .header {
                text-align: center;
                padding: 40px 20px;
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(20px);
                border-radius: 25px;
                margin-bottom: 20px;
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            .title {
                font-size: 1.8em;
                font-weight: 200;
                margin-bottom: 10px;
                background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1);
                background-size: 200% 200%;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                animation: titleGlow 3s ease-in-out infinite;
            }
            
            @keyframes titleGlow {
                0%, 100% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
            }
            
            .subtitle {
                font-size: 0.9em;
                opacity: 0.8;
                font-weight: 300;
            }
            
            /* 控制区域 */
            .controls {
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 200px;
            }
            
            /* 按钮样式 */
            .capture-btn {
                background: linear-gradient(45deg, #667eea, #764ba2);
                border: none;
                border-radius: 50px;
                padding: 18px 40px;
                font-size: 1.1em;
                color: white;
                font-weight: 300;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
                position: relative;
                overflow: hidden;
                min-width: 200px;
            }
            
            .capture-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
            }
            
            .capture-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .capture-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            
            .capture-btn:hover::before {
                left: 100%;
            }
            
            /* 加载动画 */
            .loading {
                display: none;
                text-align: center;
                margin: 30px 0;
            }
            
            .loading-spinner {
                width: 60px;
                height: 60px;
                border: 3px solid rgba(255,255,255,0.1);
                border-top: 3px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .loading-text {
                font-size: 1em;
                opacity: 0.8;
                animation: pulse 2s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 0.8; }
                50% { opacity: 0.4; }
            }
            
            /* 状态消息 */
            .status {
                margin: 20px 0;
                padding: 15px 20px;
                border-radius: 15px;
                text-align: center;
                font-size: 0.95em;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            .status.success {
                background: rgba(76, 175, 80, 0.2);
                border-color: rgba(76, 175, 80, 0.3);
                color: #4CAF50;
            }
            
            .status.error {
                background: rgba(244, 67, 54, 0.2);
                border-color: rgba(244, 67, 54, 0.3);
                color: #f44336;
            }
            
            .status.info {
                background: rgba(33, 150, 243, 0.2);
                border-color: rgba(33, 150, 243, 0.3);
                color: #2196F3;
            }
            
            .status.warning {
                background: rgba(255, 193, 7, 0.2);
                border-color: rgba(255, 193, 7, 0.3);
                color: #FFC107;
            }
            
            /* 截图显示区域 */
            .screenshot-container {
                margin-top: 30px;
                position: relative;
                border-radius: 20px;
                overflow: hidden;
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            .screenshot {
                width: 100%;
                height: auto;
                display: none;
                border-radius: 20px;
                transition: all 0.5s ease;
            }
            
            .screenshot.show {
                display: block;
                animation: fadeInScale 0.8s ease-out;
            }
            
            @keyframes fadeInScale {
                0% {
                    opacity: 0;
                    transform: scale(0.8);
                }
                100% {
                    opacity: 1;
                    transform: scale(1);
                }
            }
            
            /* 全屏查看 */
            .fullscreen-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.95);
                z-index: 1000;
                display: none;
                align-items: center;
                justify-content: center;
                backdrop-filter: blur(10px);
            }
            
            .fullscreen-image {
                max-width: 95%;
                max-height: 95%;
                border-radius: 10px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            }
            
            .close-fullscreen {
                position: absolute;
                top: 30px;
                right: 30px;
                background: rgba(255,255,255,0.2);
                border: none;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                color: white;
                font-size: 1.5em;
                cursor: pointer;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }
            
            .close-fullscreen:hover {
                background: rgba(255,255,255,0.3);
                transform: scale(1.1);
            }
            
            /* 自动状态指示器 */
            .auto-indicator {
                position: absolute;
                top: 20px;
                right: 20px;
                background: rgba(76, 175, 80, 0.2);
                color: #4CAF50;
                padding: 8px 15px;
                border-radius: 20px;
                font-size: 0.8em;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(76, 175, 80, 0.3);
                animation: pulse 2s ease-in-out infinite;
            }
            
            /* 底部提示 */
            .footer-hint {
                text-align: center;
                padding: 30px 20px;
                font-size: 0.85em;
                opacity: 0.6;
                line-height: 1.6;
            }
            
            /* 响应式设计 */
            @media (max-width: 480px) {
                .header {
                    padding: 30px 15px;
                }
                
                .title {
                    font-size: 1.5em;
                }
                
                .capture-btn {
                    padding: 15px 30px;
                    font-size: 1em;
                    min-width: 180px;
                }
            }
        </style>
    </head>
    <body>
        <!-- 动态背景 -->
        <div class="bg-animation"></div>
        
        <!-- 浮动粒子 -->
        <div class="particles" id="particles"></div>
        
        <div class="container">
            <!-- 自动模式指示器 -->
            <div class="auto-indicator" id="autoIndicator">
                🎨 自动捕捉模式
            </div>
            
            <!-- 头部 -->
            <div class="header">
                <h1 class="title">艺术瞬间</h1>
                <p class="subtitle">捕捉创作过程中的每一个精彩时刻</p>
            </div>
            
            <!-- 控制区域 -->
            <div class="controls">
                <button id="captureBtn" class="capture-btn" onclick="requestScreenshot()" style="display: none;">
                    📸 捕捉此刻
                </button>
                
                <div id="loading" class="loading">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">正在捕捉艺术瞬间...</div>
                </div>
                
                <div id="status"></div>
            </div>
            
            <!-- 截图显示 -->
            <div class="screenshot-container" id="screenshotContainer" style="display: none;">
                <img id="screenshot" class="screenshot" onclick="openFullscreen()" />
            </div>
            
            <!-- 底部提示 -->
            <div class="footer-hint">
                <p>✨ 页面将自动获取最新的艺术作品截图</p>
                <p>🔄 点击按钮可手动刷新 | 📱 点击图片可全屏查看</p>
            </div>
        </div>
        
        <!-- 全屏查看 -->
        <div class="fullscreen-overlay" id="fullscreenOverlay" onclick="closeFullscreen()">
            <img id="fullscreenImage" class="fullscreen-image" />
            <button class="close-fullscreen" onclick="closeFullscreen()">×</button>
        </div>
        
        <script>
            let currentRequestId = null;
            let pollInterval = null;
            let autoRequested = false;
            
            // 创建浮动粒子
            function createParticles() {
                const particlesContainer = document.getElementById('particles');
                const particleCount = 20;
                
                for (let i = 0; i < particleCount; i++) {
                    const particle = document.createElement('div');
                    particle.className = 'particle';
                    particle.style.left = Math.random() * 100 + '%';
                    particle.style.width = particle.style.height = (Math.random() * 4 + 2) + 'px';
                    particle.style.animationDelay = Math.random() * 20 + 's';
                    particle.style.animationDuration = (Math.random() * 10 + 15) + 's';
                    particlesContainer.appendChild(particle);
                }
            }
            
            // 页面加载完成后初始化
            window.addEventListener('load', function() {
                createParticles();
                
                setTimeout(() => {
                    if (!autoRequested) {
                        autoRequested = true;
                        requestScreenshot(true);
                    }
                }, 1000);
            });
            
            async function requestScreenshot(isAuto = false) {
                const captureBtn = document.getElementById('captureBtn');
                const loading = document.getElementById('loading');
                const status = document.getElementById('status');
                const screenshot = document.getElementById('screenshot');
                const autoIndicator = document.getElementById('autoIndicator');
                
                if (isAuto) {
                    captureBtn.style.display = 'inline-block';
                    autoIndicator.style.display = 'block';
                }
                
                captureBtn.disabled = true;
                loading.style.display = 'block';
                
                if (isAuto) {
                    status.innerHTML = '<div class="status info">🎨 自动捕捉已启动，正在连接艺术创作空间...</div>';
                } else {
                    status.innerHTML = '<div class="status info">📸 手动捕捉请求已发送，等待处理...</div>';
                }
                
                try {
                    const response = await fetch('/api/request-screenshot', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: 'art_viewer_' + Date.now() })
                    });
                    
                    if (!response.ok) {
                        throw new Error('网络连接失败');
                    }
                    
                    const data = await response.json();
                    currentRequestId = data.request_id;
                    
                    status.innerHTML = '<div class="status warning">⚡ 正在与创作设备建立连接...</div>';
                    
                    if (pollInterval) {
                        clearInterval(pollInterval);
                    }
                    pollInterval = setInterval(checkScreenshot, 1000);
                    
                    setTimeout(() => {
                        if (pollInterval) {
                            clearInterval(pollInterval);
                            captureBtn.disabled = false;
                            loading.style.display = 'none';
                            status.innerHTML = '<div class="status error">⏰ 连接超时，请检查创作设备状态</div>';
                        }
                    }, 30000);
                    
                } catch (error) {
                    captureBtn.disabled = false;
                    loading.style.display = 'none';
                    status.innerHTML = '<div class="status error">❌ 连接失败: ' + error.message + '</div>';
                    console.error('请求截图失败:', error);
                }
            }
            
            async function checkScreenshot() {
                if (!currentRequestId) return;
                
                try {
                    const response = await fetch(`/api/get-screenshot/${currentRequestId}`);
                    
                    if (!response.ok) {
                        throw new Error('获取状态失败');
                    }
                    
                    const data = await response.json();
                    
                    if (data.status === 'completed') {
                        clearInterval(pollInterval);
                        
                        const captureBtn = document.getElementById('captureBtn');
                        const loading = document.getElementById('loading');
                        const status = document.getElementById('status');
                        const screenshot = document.getElementById('screenshot');
                        const screenshotContainer = document.getElementById('screenshotContainer');
                        
                        captureBtn.disabled = false;
                        loading.style.display = 'none';
                        status.innerHTML = '<div class="status success">✨ 艺术瞬间捕捉成功！</div>';
                        
                        screenshot.src = 'data:image/png;base64,' + data.image_data;
                        screenshot.classList.add('show');
                        screenshotContainer.style.display = 'block';
                        
                        // 平滑滚动到截图
                        setTimeout(() => {
                            screenshotContainer.scrollIntoView({ 
                                behavior: 'smooth', 
                                block: 'center' 
                            });
                        }, 400);
                        
                        currentRequestId = null;
                        
                        setTimeout(() => {
                            status.innerHTML = '<div class="status success">🎭 作品已更新！可点击按钮获取最新创作</div>';
                        }, 3000);
                        
                    } else if (data.status === 'processing') {
                        const status = document.getElementById('status');
                        status.innerHTML = '<div class="status warning">🎨 创作设备正在处理请求...</div>';
                    }
                } catch (error) {
                    console.error('轮询错误:', error);
                }
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
            
            // 页面隐藏时清理定时器
            document.addEventListener('visibilitychange', function() {
                if (document.hidden && pollInterval) {
                    clearInterval(pollInterval);
                }
            });
            
            // 页面卸载时清理定时器
            window.addEventListener('beforeunload', function() {
                if (pollInterval) {
                    clearInterval(pollInterval);
                }
            });
            
            // 阻止默认的双击缩放
            document.addEventListener('touchstart', function(event) {
                if (event.touches.length > 1) {
                    event.preventDefault();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# 其余代码保持不变
@app.post("/api/request-screenshot")
async def request_screenshot(request: ScreenshotRequest):
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
        current_time = time.time()
        expired_requests = [
            req_id for req_id, req_data in screenshot_requests.items()
            if current_time - req_data["timestamp"] > 3600  # 1小时
        ]
        
        for req_id in expired_requests:
            screenshot_requests.pop(req_id, None)
            screenshots.pop(req_id, None)
        
        await asyncio.sleep(300)  # 每5分钟清理一次

@app.on_event("startup")
async def startup_event():
    # 启动清理任务
    asyncio.create_task(cleanup_expired_requests())

if __name__ == "__main__":
    print("艺术作品截图系统启动中...")
    print("请访问 http://localhost:8000 查看二维码")
    print("注意：请将代码中的 'your-server-ip' 替换为你的实际服务器IP地址")
    uvicorn.run(app, host="0.0.0.0", port=8000)