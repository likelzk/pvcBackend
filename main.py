from fastapi import FastAPI, File, UploadFile,Request
from starlette.middleware.cors import CORSMiddleware
import shutil
import os
from starlette.responses import JSONResponse
import comfyui_basic_api
import myfunction
from fastapi.staticfiles import StaticFiles

import tripo3d_basic_api

app = FastAPI()

origins = ["http://127.0.0.1:5173"]  # 也可以设置为"*"，即为所有。
BASE_URL = "http://127.0.0.1:8000"
UPLOAD_DIR = "./uploads"
OUTPUT_DIR = "./output"
# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
# 静态文件服务
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

# 设置跨域传参
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 设置允许的origins来源
    allow_credentials=True,
    allow_methods=["*"],  # 设置允许跨域的http方法，比如 get、post、put等。
    allow_headers=["*"])  # 允许跨域的headers，可以用来鉴别来源等作用。


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/excute")
async def do_excute(request: Request):
    body = await request.json()
    print(body)
    imageSrc = body.get("imageSrc").get('_value')
    print(imageSrc)
    # 将本地文件路径填充到函数执行
    file_url = await comfyui_basic_api.excute_image(imageSrc)
    # todo 要判空
    return JSONResponse(content={"message": "操作成功", "url": file_url})

# 从前端拿到后端图片存储的位置
@app.post("/threeDexcute")
async def do_3Dexcute(request: Request):
    print("我是3D接口")
    # body = await request.json()
    # print(body)
    # imageSrc = body.get("imageSrc").get('_value')
    # print(imageSrc)
    # # 将本地文件路径填充到函数执行
    # file_url = await tripo3d_basic_api.excute_image(imageSrc)
    # # todo 要判空
    # return JSONResponse(content={"message": "操作成功", "url": file_url})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 文件保存路径
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 返回图片的 URL
    file_url = f"./uploads/{file.filename}"
    return JSONResponse(content={"message": "上传成功", "url": file_url})
