# 使用官方 Python 作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制需求文件并安装依赖
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 运行 FastAPI 应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]