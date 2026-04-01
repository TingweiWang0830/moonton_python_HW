# 基础镜像：官方 Python 3.10 精简版，体积小、够用
FROM python:3.10-slim

# 设置容器内工作目录，后续所有命令都在 /app 下执行
WORKDIR /app

# 先单独复制 requirements.txt，利用 Docker 层缓存：
# 只要依赖没变，下次构建时这一层直接复用，不重新 pip install
COPY requirements.txt .

# 安装依赖，--no-cache-dir 避免缓存占用镜像空间
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目源码（.dockerignore 会排除 .env、__pycache__ 等）
COPY . .

# 容器启动时执行的命令：运行定时任务主程序
CMD ["python", "main.py"]
