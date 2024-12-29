import base64
import os
import sys

from fastapi import File, UploadFile
import asyncio
import json
from time import sleep
from urllib import request, parse
import random

import aiohttp
import requests
from charset_normalizer.md__mypyc import exports


# This is the ComfyUI api prompt format.

# If you want it for a specific workflow you can "enable dev mode options"
# in the settings of the UI (gear beside the "Queue Size: ") this will enable
# a button on the UI to save workflows in api format.

# keep in mind ComfyUI is pre alpha software so this format will change a bit.


# 响应结果是str
# 例子：{"prompt_id": "516b76a9-ad77-4378-8750-ebd6df920851", "number": 25, "node_errors": {}}
async def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    # 异步 HTTP 请求
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("http://127.0.0.1:6006/prompt", data=data,
                                    headers={"Content-Type": "application/json"}) as response:
                # 检查响应状态码
                if response.status == 200:
                    prompt_result = await response.text()
                    print("请求成功:", prompt_result)
                    return prompt_result
                else:
                    print(f"queue promt请求失败: 状态码 {response.status}")
                    error_message = await response.text()
                    print("错误详情:", error_message)
                    return None
        except aiohttp.ClientError as e:
            print("HTTP 请求异常:", str(e))
            return None


async def get_prompt_result(promptId):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://127.0.0.1:6006/history/{}".format(promptId)) as response:
                if response.status == 200:
                    result = await response.json()
                    # 响应内容为空直接退出函数
                    print(result)
                    if not result:
                        return None
                    # 不判空容易空指针循环
                    completed = result.get(promptId).get("status").get("completed")  # 检查任务状态
                    status_str = result.get(promptId).get("status").get("status_str")
                    # 完成并且成功则返回结果
                    if completed:
                        if status_str == "success":
                            return result  # 任务完成，返回结果
                        else:
                            print("任务失败:", result)
                            return None
                    else:
                        return None  # 状态未完成
                else:
                    print(f"获取状态失败: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            print("HTTP 请求异常:", str(e))
            return None


# 将图片上传到comfyui服务器
# 成功返回图片在服务器的地址
async def upload_images(file_path: str):
    async with aiohttp.ClientSession() as session:
        try:
            with open(file_path, "rb") as image_file:
                # 构造多部分表单
                form_data = aiohttp.FormData()
                form_data.add_field(
                    name="image",  # 键名称为 `image`
                    value=image_file,  # 图片文件对象
                    filename=os.path.basename(file_path),  # 文件名
                    content_type="image/png",  # 文件类型
                )

                async with session.post("http://127.0.0.1:6006/upload/image", data=form_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        # 响应内容为空直接退出函数
                        print(result)
                        if not result:
                            return None
                        else:
                            # result = json.loads(result)
                            # autodl-tmp/ComfyUI/input
                            image_in_comfy_url = "/root/autodl-tmp/ComfyUI/input/{}".format(result.get("name"))
                            print(image_in_comfy_url)
                            return image_in_comfy_url
                    else:
                        print(f"获取状态失败: {response.status}")
                        return None
        except aiohttp.ClientError as e:
            print("HTTP 请求异常:", str(e))
            return None


# 用来获得返回图片名称
# 返回
# {
#         "outputs": outputs,
#         "filename": filename,
#     }
async def get_image_name(promptId):
    # todo 这里还应该添加判空等逻辑
    result = await get_prompt_result(promptId)
    # 用来拿到图片地址
    outputs = result.get(promptId).get("outputs")
    filename = outputs.get("181").get("images")[0].get("filename")
    # subfolder = outputs.get("181").get("image").get("subfolder")

    # imageName = result.get(promptId).get("outputs").get("33").get("images")[0].get("filename")
    print("outImageMessage:", filename)
    return filename


# 获得图片
async def get_images(imageName):
    # 异步请求图片数据
    async with aiohttp.ClientSession() as session:
        async with session.get("http://127.0.0.1:6006/view?filename={}".format(imageName)) as response:
            if response.status == 200:
                # 解析文件名（从 Content-Disposition 或 URL 提取）
                content_disposition = response.headers.get("Content-Disposition")
                if content_disposition and "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1].strip('"')
                else:
                    # 默认使用 prompt_id 作为文件名
                    filename = imageName

                # 文件保存路径
                file_location = os.path.join(".\output", filename)
                os.makedirs(os.path.dirname(file_location), exist_ok=True)

                # 保存文件到本地
                with open(file_location, "wb") as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        #     todo 这里加await试试
                        f.write(chunk)

                print(f"文件已保存到: {file_location}")
                # 网络请求地址
                # todo 这里应该能将base地址提出来为公共变量的
                file_net_location = os.path.join("http://127.0.0.1:8000/output/", filename)
                return file_net_location
            else:
                print(f"请求失败，状态码: {response.status}")
                return None


# 将图片高清处理，返回高清图片内容
# todo 拿到图片正确返回
async def excute_image(imageSrc: str):
    # this is the one for the default workflow
    # todo将json文件转为字符串赋值  || 或者直接加载json字符串？
    # 拿到上传后的文件名
    imageSrc = await upload_images(imageSrc)
    prompt_text = """
    {
  "2": {
    "inputs": {
      "ckpt_name": "PVCStyleModelDreamy_beta12.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {
      "title": "Checkpoint加载器(简易)"
    }
  },
  "6": {
    "inputs": {
      "image": "林泽楷.jpg",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "加载图像"
    }
  },
  "12": {
    "inputs": {
      "width": 512,
      "height": 768,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage",
    "_meta": {
      "title": "空Latent"
    }
  },
  "68": {
    "inputs": {
      "instantid_file": "ip-adapter_instant_id_sdxl.bin"
    },
    "class_type": "InstantIDModelLoader",
    "_meta": {
      "title": "InstnatID模型加载器"
    }
  },
  "69": {
    "inputs": {
      "control_net_name": "control_instant_id_sdxl.safetensors"
    },
    "class_type": "ControlNetLoader",
    "_meta": {
      "title": "ControlNet加载器"
    }
  },
  "71": {
    "inputs": {
      "provider": "CUDA"
    },
    "class_type": "InstantIDFaceAnalysis",
    "_meta": {
      "title": "InstantID面部分析"
    }
  },
  "77": {
    "inputs": {
      "weight": 0.8,
      "start_at": 0.2,
      "end_at": 1,
      "instantid": [
        "68",
        0
      ],
      "insightface": [
        "71",
        0
      ],
      "control_net": [
        "69",
        0
      ],
      "image": [
        "172",
        0
      ],
      "positive": [
        "118",
        0
      ],
      "negative": [
        "119",
        0
      ],
      "image_kps": [
        "145",
        5
      ],
      "model": [
        "195",
        0
      ]
    },
    "class_type": "ApplyInstantID",
    "_meta": {
      "title": "应用InstantID"
    }
  },
  "114": {
    "inputs": {
      "pulid_file": "ip-adapter_pulid_sdxl_fp16.safetensors"
    },
    "class_type": "PulidModelLoader",
    "_meta": {
      "title": "PuLID模型加载器"
    }
  },
  "115": {
    "inputs": {},
    "class_type": "PulidEvaClipLoader",
    "_meta": {
      "title": "PuLIDEVAClip加载器"
    }
  },
  "116": {
    "inputs": {
      "provider": "CUDA"
    },
    "class_type": "PulidInsightFaceLoader",
    "_meta": {
      "title": "PuLIDInsightFace加载器"
    }
  },
  "118": {
    "inputs": {
      "text": [
        "122",
        0
      ],
      "clip": [
        "195",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP文本编码器"
    }
  },
  "119": {
    "inputs": {
      "text": "nsfw, paintings, cartoon, anime, sketches, worst quality, low quality, normal quality, lowres, watermark, monochrome, grayscale, ugly, blurry, Tan skin, dark skin, black skin, skin spots, skin blemishes, age spot, glans, disabled, distorted, bad anatomy, morbid, malformation, amputation, bad proportions, twins, missing body, fused body, extra head, poorly drawn face, bad eyes, deformed eye, unclear eyes, cross-eyed, long neck, malformed limbs, extra limbs, extra arms, missing arms, bad tongue, strange fingers, mutated hands, missing hands, poorly drawn hands, extra hands, fused hands, connected hand, bad hands, wrong fingers, missing fingers, extra fingers, 4 fingers, 3 fingers, deformed hands, extra legs, bad legs, many legs, more than two legs, bad feet, wrong feet, extra feets,",
      "clip": [
        "195",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP文本编码器"
    }
  },
  "120": {
    "inputs": {
      "text": "(whole body:1.5)，(masterpiece),(highest quality),(extremely detailed),Anime,(extremely detailed),(figurine:1.5),(((solo))),(whole body shot:1.5), (whole-length portrait:1.5),exaggerated features with, oversized features, ((dark background, clean background)),"
    },
    "class_type": "CR Text",
    "_meta": {
      "title": "文本"
    }
  },
  "122": {
    "inputs": {
      "text_1": [
        "120",
        0
      ],
      "text_2": [
        "163",
        0
      ]
    },
    "class_type": "ConcatText_Zho",
    "_meta": {
      "title": "✨ConcatText_Zho"
    }
  },
  "137": {
    "inputs": {
      "side_length": 1024,
      "side": "Longest",
      "upscale_method": "nearest-exact",
      "crop": "disabled",
      "image": [
        "6",
        0
      ]
    },
    "class_type": "DF_Image_scale_to_side",
    "_meta": {
      "title": "Image scale to side"
    }
  },
  "138": {
    "inputs": {
      "method": "fidelity",
      "weight": 1,
      "start_at": 0,
      "end_at": 0.9,
      "model": [
        "143",
        0
      ],
      "pulid": [
        "114",
        0
      ],
      "eva_clip": [
        "115",
        0
      ],
      "face_analysis": [
        "116",
        0
      ],
      "image": [
        "137",
        0
      ]
    },
    "class_type": "ApplyPulid",
    "_meta": {
      "title": "应用PuLID"
    }
  },
  "140": {
    "inputs": {
      "preset": "VIT-G (medium strength)",
      "model": [
        "195",
        0
      ]
    },
    "class_type": "IPAdapterUnifiedLoader",
    "_meta": {
      "title": "IPAdapter加载器"
    }
  },
  "141": {
    "inputs": {
      "interpolation": "LANCZOS",
      "crop_position": "pad",
      "sharpening": 0,
      "image": [
        "137",
        0
      ]
    },
    "class_type": "PrepImageForClipVision",
    "_meta": {
      "title": "CLIP视觉图像处理"
    }
  },
  "143": {
    "inputs": {
      "weight": 0.8,
      "weight_type": "ease in",
      "combine_embeds": "concat",
      "start_at": 0.3,
      "end_at": 0.6,
      "embeds_scaling": "V only",
      "model": [
        "140",
        0
      ],
      "ipadapter": [
        "140",
        1
      ],
      "image": [
        "137",
        0
      ]
    },
    "class_type": "IPAdapterAdvanced",
    "_meta": {
      "title": "应用IPAdapter（高级）"
    }
  },
  "145": {
    "inputs": {
      "seed": 55,
      "steps": 15,
      "cfg": 4,
      "sampler_name": "euler_ancestral",
      "scheduler": "karras",
      "denoise": 1,
      "preview_method": "auto",
      "vae_decode": "true",
      "model": [
        "138",
        0
      ],
      "positive": [
        "118",
        0
      ],
      "negative": [
        "119",
        0
      ],
      "latent_image": [
        "12",
        0
      ],
      "optional_vae": [
        "2",
        2
      ]
    },
    "class_type": "KSampler (Efficient)",
    "_meta": {
      "title": "K采样器(效率)"
    }
  },
  "146": {
    "inputs": {
      "images": [
        "145",
        5
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "预览图像"
    }
  },
  "151": {
    "inputs": {
      "seed": 889444428909982,
      "steps": 20,
      "cfg": 4,
      "sampler_name": "euler_ancestral",
      "scheduler": "karras",
      "denoise": 0.6,
      "preview_method": "auto",
      "vae_decode": "true",
      "model": [
        "77",
        0
      ],
      "positive": [
        "77",
        1
      ],
      "negative": [
        "77",
        2
      ],
      "latent_image": [
        "182",
        0
      ],
      "optional_vae": [
        "2",
        2
      ],
      "script": [
        "183",
        0
      ]
    },
    "class_type": "KSampler (Efficient)",
    "_meta": {
      "title": "K采样器(效率)"
    }
  },
  "163": {
    "inputs": {
      "text": [
        "164",
        0
      ],
      "text2": "a young man with black hair and dark brown eyes"
    },
    "class_type": "ShowText|pysssss",
    "_meta": {
      "title": "展示文本"
    }
  },
  "164": {
    "inputs": {
      "question": "describe this character,Gender, skin colour, hairstyle,dresses. this is really important to my career.",
      "image": [
        "137",
        0
      ]
    },
    "class_type": "LayerUtility: QWenImage2Prompt",
    "_meta": {
      "title": "LayerUtility: QWenImage2Prompt(Advance)"
    }
  },
  "166": {
    "inputs": {
      "images": [
        "141",
        0
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "预览图像"
    }
  },
  "167": {
    "inputs": {
      "confidence": 0.1,
      "margin": 100,
      "model": [
        "169",
        0
      ],
      "image": [
        "137",
        0
      ]
    },
    "class_type": "Crop Face",
    "_meta": {
      "title": "Crop Face"
    }
  },
  "168": {
    "inputs": {
      "images": [
        "172",
        0
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "预览图像"
    }
  },
  "169": {
    "inputs": {},
    "class_type": "Load RetinaFace",
    "_meta": {
      "title": "Load RetinaFace"
    }
  },
  "172": {
    "inputs": {
      "side_length": 1024,
      "side": "Longest",
      "upscale_method": "nearest-exact",
      "crop": "disabled",
      "image": [
        "167",
        0
      ]
    },
    "class_type": "DF_Image_scale_to_side",
    "_meta": {
      "title": "Image scale to side"
    }
  },
  "181": {
    "inputs": {
      "filename_prefix": "PVC-Figures-You",
      "images": [
        "151",
        5
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "保存图像"
    }
  },
  "182": {
    "inputs": {
      "upscale_method": "nearest-exact",
      "scale_by": 1.5,
      "samples": [
        "145",
        3
      ]
    },
    "class_type": "LatentUpscaleBy",
    "_meta": {
      "title": "Latent按系数缩放"
    }
  },
  "183": {
    "inputs": {
      "upscale_type": "latent",
      "hires_ckpt_name": "(use same)",
      "latent_upscaler": "nearest-exact",
      "pixel_upscaler": "RealESRGAN_x4plus.pth",
      "upscale_by": 1.5,
      "use_same_seed": true,
      "seed": 369763404839180,
      "hires_steps": 8,
      "denoise": 0.5,
      "iterations": 1,
      "use_controlnet": false,
      "control_net_name": "control_instant_id_sdxl.safetensors",
      "strength": 1,
      "preprocessor": "none",
      "preprocessor_imgs": false
    },
    "class_type": "HighRes-Fix Script",
    "_meta": {
      "title": "高清修复"
    }
  },
  "191": {
    "inputs": {
      "MODEL": [
        "195",
        0
      ],
      "CLIP": [
        "195",
        1
      ],
      "VAE": [
        "2",
        2
      ]
    },
    "class_type": "Anything Everywhere3",
    "_meta": {
      "title": "全局输入3"
    }
  },
  "195": {
    "inputs": {
      "lora_name": "EnvyZoomSliderXL01.safetensors",
      "strength_model": -1.25,
      "strength_clip": 1,
      "model": [
        "2",
        0
      ],
      "clip": [
        "2",
        1
      ]
    },
    "class_type": "LoraLoader",
    "_meta": {
      "title": "LoRA加载器"
    }
  }
}
    """

    prompt = json.loads(prompt_text)
    print(prompt)
    # set the text prompt for our loading image
    # imageSource = "G:\Picture\pexels-photo-2049422.jpeg"
    # "145": {
    #     "inputs": {
    #       "seed": 55,
    # todo 这里有问题，图片应为服务器本地图片
    prompt["6"]["inputs"]["image"] = imageSrc
    max_num = sys.maxsize
    randon_num = random.randint(0, max_num)
    prompt["145"]["inputs"]["seed"] = randon_num
    print(prompt)

    prompt_id_result = await queue_prompt(prompt)

    # 如果放入队列成功，json化响应值以方便取prompt_id
    if prompt_id_result:
        prompt_id_result = json.loads(prompt_id_result)
        print("响应结果:", prompt_id_result.get("prompt_id"))

    result = {}

    image_name = ""

    while not result:
        print("等待任务完成...")
        await asyncio.sleep(2)  # 等待 2 秒
        result = await get_prompt_result(prompt_id_result.get("prompt_id"))

    # 拿到处理后的图像名
    image_name = await get_image_name(prompt_id_result.get("prompt_id"))
    # 根据文件名向后端请求回传文件
    file_location = await get_images(image_name)

    # print("最终任务结果:", result)
    return file_location

# 启动异步主函数
# if __name__ == "__main__":
# asyncio.run(main())
# 可能是本地上传的图片在服务端不能被访问到
# asyncio.run(excute_image("./uploads/picture1.jpg"))
#     asyncio.run(upload_images("./uploads/ab2f52f4d7510fde33a3dba1ae60a786.jpg"))
# asyncio.run(get_prompt_result("6799352e-248d-471d-8b01-d64700953028"))
# asyncio.run(get_image_name("a7e8ccd4-193b-4716-b33d-ebab851bc9df"))
# asyncio.run(get_images("._00001_.png"))
