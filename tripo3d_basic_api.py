# 只适应tripo3d模型1.n版本

import asyncio
import json
import os
import uuid
from urllib import response

import aiohttp
import requests
from tqdm import tqdm
from pydantic import BaseModel


# type: # This field must be set to image_to_model.
#
# model_version (Optional): Model version. Available versions are as below:
#
# default
# v2.0-20240919
# v1.4-20240625
# v1.3-20240522
# default is v1.4-20240625
#
# file: Specifies the image input.
#
# type: # Indicates the file type. Although currently not validated, specifying the correct file type is strongly advised.
# file_token: The identifier you get from upload, please read Docs/Upload. Mutually exclusive with url.
# url: A direct URL to the image. Supports JPEG and PNG formats with maximum size of 20MB. Mutually exclusive with file_token.
# model_seed (Optional): This is the random seed for model generation. In version v2.0-20240919, the seed controls the geometry generation process, ensuring identical models when the same seed is used. This parameter is an integer and is randomly chosen if not set.


# 将图片上传到tripo3D服务器
# 参数:本地图片地址
# 返回格式：{'code': 0, 'data': {'image_token': 'a106678e-e741-420f-86d9-77a1d11ee4d2'}}
# 返回文件地址外，还要返回文件格式
async def upload_images(file_path: str):
    async with aiohttp.ClientSession() as session:
        try:
            with open(file_path, "rb") as image_file:
                # 构造多部分表单
                form_data = aiohttp.FormData()
                form_data.add_field(
                    name="file",  # 键名称为 `image`
                    value=image_file,  # 图片文件对象
                    filename=os.path.basename(file_path),  # 文件名
                    # 逐一排查，这里后面要改多一个jpeg格式
                    content_type="image/png,image/jpeg",  # 文件类型
                )

                headers = {
                    "Authorization": "Bearer tsk_eehpLR1NhII4RIcsoZXFxSJHahcqeJprdttrSix-t8j"
                }

                async with session.post("https://api.tripo3d.ai/v2/openapi/upload", data=form_data,
                                        headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        # 响应内容为空直接退出函数
                        print(result)
                        if not result:
                            return None
                        else:
                            # result = json.loads(result)
                            image_key = result.get("data").get("image_token")
                            print(image_key)
                            return image_key
                    else:
                        print(f"获取状态失败: {response.status}")
                        return None
        except aiohttp.ClientError as e:
            print("HTTP 请求异常:", str(e))
            return None


# 给tripo3d添加处理，拿到任务号
async def put_task(type: str, file_token: str):
    async with aiohttp.ClientSession() as session:
        try:
            # 返回体
            # {
            #     "code": 0,
            #     "data": {
            #         "task_id": "6a41962f-7e86-425a-b98b-97cccb2095f2"
            #     }
            # }
            p = {
                "type": "image_to_model",
                "file": {
                    "type": "",
                    "file_token": ""
                }
            }

            p["file"]["type"] = type
            p["file"]["file_token"] = file_token

            data = json.dumps(p).encode('utf-8')
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer tsk_eehpLR1NhII4RIcsoZXFxSJHahcqeJprdttrSix-t8j"
            }
            async with session.post("https://api.tripo3d.ai/v2/openapi/task", data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    # 响应内容为空直接退出函数
                    print(result)
                    if not result:
                        return None
                    else:
                        # result = json.loads(result)
                        task_id = result.get("data").get("task_id")
                        print(task_id)
                        return task_id
                else:
                    print(f"获取状态失败: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            print("HTTP 请求异常:", str(e))
            return None


# 返回体示例：
# {
#     "code": 0,
#     "data": {
#         "task_id": "6a41962f-7e86-425a-b98b-97cccb2095f2",
#         "type": "image_to_model",
#         "status": "success",
#         "input": {
#             "model_version": "v1.4-20240625",
#             "file": {
#                 "type": "png",
#                 "object": {
#                     "bucket": "tripo-data",
#                     "key": "tcli_7e4b5eb00c45490cad3d56a0348d444f/20241226/6a41962f-7e86-425a-b98b-97cccb2095f2/image.png"
#                 }
#             },
#             "texture": true,
#             "pbr": true
#         },
#         "output": {
#             "model": "https://tripo-data.cdn.bcebos.com/tcli_7e4b5eb00c45490cad3d56a0348d444f/20241226/6a41962f-7e86-425a-b98b-97cccb2095f2/tripo_draft_6a41962f-7e86-425a-b98b-97cccb2095f2.glb?auth_key=1735257600-1db7y1WW-0-2d56cfa86753143006e17f38dd8eb0e6",
#             "rendered_image": "https://tripo-data.cdn.bcebos.com/tcli_7e4b5eb00c45490cad3d56a0348d444f/20241226/6a41962f-7e86-425a-b98b-97cccb2095f2/rendered_image.webp?auth_key=1735257600-1db7y1WW-0-4a9a6afc8f79fc7e59f36d7e72291222"
#         },
#         "progress": 100,
#         "create_time": 1735203566,
#         "thumbnail": "https://tripo-data.cdn.bcebos.com/tcli_7e4b5eb00c45490cad3d56a0348d444f/20241226/6a41962f-7e86-425a-b98b-97cccb2095f2/rendered_image.webp?auth_key=1735257600-1db7y1WW-0-4a9a6afc8f79fc7e59f36d7e72291222",
#         "queuing_num": -1,
#         "running_left_time": -1,
#         "result": {
#             "model": {
#                 "url": "https://tripo-data.cdn.bcebos.com/tcli_7e4b5eb00c45490cad3d56a0348d444f/20241226/6a41962f-7e86-425a-b98b-97cccb2095f2/tripo_draft_6a41962f-7e86-425a-b98b-97cccb2095f2.glb?auth_key=1735257600-1db7y1WW-0-2d56cfa86753143006e17f38dd8eb0e6",
#                 "type": "glb"
#             },
#             "rendered_image": {
#                 "type": "webp",
#                 "url": "https://tripo-data.cdn.bcebos.com/tcli_7e4b5eb00c45490cad3d56a0348d444f/20241226/6a41962f-7e86-425a-b98b-97cccb2095f2/rendered_image.webp?auth_key=1735257600-1db7y1WW-0-4a9a6afc8f79fc7e59f36d7e72291222"
#             }
#         }
#     }
# }
# 根据任务号拿到模型等东西，实际可根据需要扩展
async def get_result(task_id: str):
    async with aiohttp.ClientSession() as session:
        try:
            headers = {
                "Authorization": "Bearer tsk_eehpLR1NhII4RIcsoZXFxSJHahcqeJprdttrSix-t8j"
            }
            async with session.get("https://api.tripo3d.ai/v2/openapi/task/{}".format(task_id), headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    # 响应内容为空直接退出函数
                    print(result)
                    if not result:
                        return None
                    # 不判空容易空指针循环
                #    直接返回结果
                    return result
                else:
                    print(f"获取状态失败: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            print("HTTP 请求异常:", str(e))
            return None


async def get_images(imageUrl):
    file_location = "./threeDOutput"
    file_name = imageUrl.split('/')[-1].split('?')[0]
    file_location = os.path.join(".\\threeDOutput", file_name)

    # 发送 GET 请求，设置 stream=True 以便分块下载
    response = requests.get(imageUrl, stream=True)
    response.raise_for_status()  # 检查请求是否成功

    # 获取文件总大小（字节）
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 每次下载 1KB
    t = tqdm(total=total_size, unit='iB', unit_scale=True)

    with open(file_location, 'wb') as file:
        for data in response.iter_content(block_size):
            t.update(len(data))
            file.write(data)
    t.close()

    if total_size != 0 and t.n != total_size:
        print("警告：下载可能未完成或被中断。")
    else:
        print(f"文件已成功下载并保存为 {file_location}")

    return file_location

async def excute(file_path: str):
    image_key = await upload_images(file_path)
#     判空？
    task_id = await put_task("image", image_key)

    result = await get_result(task_id)

    while result.get("data").get("status") != "success":
        result = await get_result(task_id)

    final_url = result.get("data").get("output").get("model")
    file_location = await get_images(final_url)
    # 返回3D模型在后端的地址
    print(file_location)

    return file_location



# 启动异步主函数
# if __name__ == "__main__":
    # asyncio.run(main())
    # asyncio.run(get_image_message("06ed7956-eca4-4c0c-a723-5623948ff9ea"))
    # 可能是本地上传的图片在服务端不能被访问到
    # asyncio.run(excute_image("./uploads/picture1.jpg"))
    # asyncio.run(upload_images("./uploads/picture1.jpg"))
    # asyncio.run(upload_images("./uploads/wallhaven-werdv6.png"))
    # asyncio.run(put_task("image/png","a106678e-e741-420f-86d9-77a1d11ee4d2"))
    # asyncio.run(get_result("de4efb51-8f5a-4c0a-998f-bb1cfa91cb79"))
    # asyncio.run(excute("./uploads/林泽楷.jpg"))
    # asyncio.run(get_images("https://tripo-data.cdn.bcebos.com/tcli_7e4b5eb00c45490cad3d56a0348d444f/20241228/5fd77fe0-5c5c-48c4-9277-79585d524ed0/tripo_draft_5fd77fe0-5c5c-48c4-9277-79585d524ed0.glb?auth_key=1735430400-eJ7ADvQd-0-00f541ebf60a4a0b518000fd0350321a"))

