import os
import shutil

from fastapi import UploadFile,File

UPLOAD_DIR = "./uploads"

async def upload_file(file: UploadFile = File(...)):
    # 文件保存路径
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 返回图片的 URL
    file_url = f"./uploads/{file.filename}"
    return file_url