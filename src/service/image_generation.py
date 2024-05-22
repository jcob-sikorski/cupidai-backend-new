from fastapi import BackgroundTasks, HTTPException

from typing import Dict, List, Optional

from uuid import uuid4

import os

import re

from pyuploadcare import Uploadcare

import requests

from comfyui.ModelInterface import generate_workflow

import data.image_generation as data

from model.account import Account
from model.image_generation import Settings, Message

import service.billing as billing_service
import service.usage_history as usage_history_service

def webhook(message: Message) -> None:
    print(message)
    update_message(user_id=message.user_id, 
                   message_id=message.message_id, 
                   status=message.status, 
                   s3_uris=message.s3_uris)

    if message.status == 'in progress':
        usage_history_service.update('image_generation', message.user_id)

def check_settings(settings: Settings):
    samplers = [
        "euler",
        "euler_ancestral",
        "heun",
        "heunpp2",
        "dpm_2",
        "dpm_2_ancestral",
        "Ims",
        "dpm_fast",
        "dpm_adaptive",
        "dpmpp_2s_ancestral",
        "dpmpp_sde",
        "dpmpp_sde_gpu",
        "dpmpp_2m",
        "dpmpp_2m_sde",
        "dpmpp_2m_sde_gpu",
        "dpmpp_3m_sde",
        "dpmpp_3m_sde_gpu",
        "ddpm",
        "lcm",
        "ddim",
        "uni_pc",
        "uni_pc_bh2"
    ]

    checkpoint_models = [
        'amIReal_V44.safetensors', 
        'analogMadness_v60.safetensors', 
        'chilloutmix_NiPrunedFp32Fix.safetensors', 
        'consistentFactor_euclidV61.safetensors', 
        'devlishphotorealism_v40.safetensors', 
        'edgeOfRealism_eorV20Fp16BakedVAE.safetensors', 
        'epicphotogasm_lastUnicorn.safetensors', 
        'epicrealism_naturalSinRC1.safetensors', 
        'epicrealism_newCentury.safetensors', 
        'juggernaut_reborn.safetensors', 
        'metagodRealRealism_v10.safetensors', 
        'realismEngineSDXL_v10.safetensors', 
        'realisticVisionV51_v51VAE.safetensors', 
        'stablegramUSEuropean_v21.safetensors', 
        'uberRealisticPornMerge_urpmv13.safetensors'
    ]

    ipa_models = [
        'ip-adapter-plus-face_sd15.bin', 
        'ip-adapter-plus_sd15.bin', 
        'ip-adapter-plus_sdxl_vit-h.bin', 
        'ip-adapter_sd15_light.bin', 
        'ip-adapter_sdxl.bin', 
        'ip-adapter_sdxl_vit-h.bin'
    ]

    controlnet_models = []

    lora_models = [
        "add_detail.safetensors",
        "age_slider_v20.safetensors",
        "analogFilmPhotography_10.safetensors",
        "beard_slider_v10.safetensors",
        "contrast_slider_v10.safetensors",
        "curly_hair_slider_v1.safetensors",
        "DarkLighting.safetensors",
        "depth_of_field_slider_v1.safetensors",
        "detail_slider_v4.safetensors",
        "emotion_happy_slider_v1.safetensors",
        "eyebrows_slider_v2.safetensors",
        "filmgrain_slider_v1.safetensors",
        "fisheye_slider_v10.safetensors",
        "gender_slider_v1.safetensors",
        "lora_perfecteyes_v1_from_v1_160.safetensors",
        "muscle_slider_v1.safetensors",
        "people_count_slider_v1.safetensors",
        "skin_tone_slider_v1.safetensors",
        "time_slider_v1.safetensors",
        "Transparent_Clothes_V2.safetensors",
        "weight_slider_v2.safetensors"
    ]
        
    if settings.basic_sampling_steps and settings.basic_sampling_steps > 120:
        return "Error: basic_sampling_steps must be less than or equal to 120"

    if settings.basic_sampler_method and settings.basic_sampler_method not in samplers:
        return f"Error: basic_sampler_method must be one of {samplers}"

    if settings.basic_model and settings.basic_model not in checkpoint_models:
        return f"Error: basic_model must be one of {checkpoint_models}"

    if settings.basic_cfg_scale and settings.basic_cfg_scale > 100.0:
        return "Error: basic_cfg_scale must be less than or equal to 100.0"

    if settings.basic_batch_size and not (1 <= settings.basic_batch_size <= 8):
        return "Error: basic_batch_size must be between 1 and 8"

    if settings.basic_batch_count and not (1 <= settings.basic_batch_count <= 4):
        return "Error: basic_batch_count must be between 1 and 4"

    if settings.basic_denoise and settings.basic_denoise > 1.0:
        return "Error: basic_denoise must be less than or equal to 1.0"

    if settings.ipa_1_model and settings.ipa_1_model not in ipa_models:
        return f"Error: ipa_1_model must be one of {ipa_models}"

    if settings.ipa_1_weight and settings.ipa_1_weight > 1.0: # TODO: weight is -1 to 3
        return "Error: ipa_1_weight must be less than or equal to 1.0"
    
    if settings.ipa_1_noise and settings.ipa_1_noise > 1.0:
        return "Error: ipa_1_noise must be less than or equal to 1.0"

    if settings.basic_sampling_steps and settings.ipa_1_start_at and settings.ipa_1_end_at and (settings.ipa_1_start_at > 1.0 or settings.ipa_1_start_at >= settings.ipa_1_end_at):
        return "Error: ipa_1_start_at must be less than or equal to 1.0 and less than ipa_1_end_at"

    if settings.ipa_1_end_at and settings.ipa_1_end_at > 1.0:
        return "Error: ipa_1_end_at must be less than or equal to 1.0"

    if settings.ipa_2_model and settings.ipa_2_model not in ipa_models:
        return f"Error: ipa_2_model must be one of {ipa_models}"

    if settings.ipa_2_weight and settings.ipa_2_weight > 1.0:
        return "Error: ipa_2_weight must be less than or equal to 1.0"

    if settings.ipa_2_noise and settings.ipa_2_noise > 1.0:
        return "Error: ipa_2_noise must be less than or equal to 1.0"

    if settings.basic_sampling_steps and settings.ipa_2_start_at and settings.ipa_2_end_at and (settings.ipa_2_start_at > 1.0 or settings.ipa_2_start_at >= settings.ipa_2_end_at):
        return "Error: ipa_2_start_at must be less than or equal to 1.0 and less than ipa_2_end_at"

    if settings.basic_sampling_steps and settings.ipa_2_end_at and settings.ipa_2_end_at > 1.0:
        return "Error: ipa_2_end_at must be less than or equal to 1.0"

    if settings.refinement_steps and settings.refinement_steps > 120:
        return "Error: refinement_steps must be less than or equal to 120"

    if settings.refinement_cfg_scale and settings.refinement_cfg_scale > 100.0:
        return "Error: refinement_cfg_scale must be less than or equal to 100.0"
    
    if settings.refinement_denoise and settings.refinement_denoise > 1.0:
        return "Error: refinement_denoise must be less than or equal to 1.0"

    if settings.refinement_sampler and settings.refinement_sampler not in samplers:
        return f"Error: refinement_sampler must be one of {samplers}"

    if settings.lora_count and not (1 <= settings.lora_count <= 4):
        return "Error: lora_count must be between 1 and 4"
    
    if settings.lora_models:
        for model in settings.lora_models:
            if model not in lora_models:
                return f"Error: lora_model must be one of lora_models."

    if settings.lora_strengths and any(map(lambda x: x > 10.0, settings.lora_strengths)):
        return "Error: All values in lora_strengths must be greater than 10.0"
    
    if settings.civitai_model and settings.civitai_model not in checkpoint_models:
        return f"Error: civitai_model must be one of {checkpoint_models}"
    
    return True

def save_settings(settings: Settings):
    return data.save_settings(settings)

def update_message(user_id: str, 
                   status: Optional[str] = None, 
                   uploadcare_uris: Optional[List[str]] = None, 
                   message_id: Optional[str] = None, 
                   settings_id: Optional[str] = None, 
                   s3_uris: Optional[List[str]] = None):
    return data.update_message(user_id, 
                               status, 
                               uploadcare_uris, 
                               message_id, 
                               settings_id, 
                               s3_uris)

def extract_id_from_uri(uri):
    # Use regex to extract the UUID from the URI
    match = re.search(r"/([a-f0-9-]+)/", uri)
    if match:
        return match.group(1)
    else:
        return None
    
def send_post_request(url: str, headers: dict, payload: dict) -> None:
    requests.post(url, headers=headers, json=payload)

async def generate(settings: Settings, 
                   user: Account, 
                   background_tasks: BackgroundTasks) -> None:
    if billing_service.has_permissions("Realistic AI Content Creation", user):
        check = check_settings(settings)
        if check is not True:
            # print("CHECK: ", check)
            raise HTTPException(status_code=400, detail=check)

        uploadcare = Uploadcare(public_key=os.getenv('UPLOADCARE_PUBLIC_KEY'), secret_key=os.getenv('UPLOADCARE_SECRET_KEY'))

        uploadcare_uris = [settings.ipa_1_reference_image, settings.ipa_2_reference_image]
        # print("UPLOADCARE URIS", uploadcare_uris)

        image_formats = []
        image_ids = []
        for i in range(2):
            if uploadcare_uris[i]:
                uploadcare_id = extract_id_from_uri(uploadcare_uris[i])
                
                image_formats.append(uploadcare.file(uploadcare_id).info['mime_type'].split('/')[1])

                image_ids.append(uploadcare_id)
            else:
                image_formats.append('')
                image_ids.append('')

        # print("IMAGE IDS", image_ids)
        # print("IMAGE FORMATS", image_formats)

        if any(ext and ext not in ['jpeg', 'png', 'heic'] for ext in image_formats):
            raise HTTPException(status_code=400, detail="Invalid image format. Valid ones are jpeg, png, heic.")

        # settings_id = save_settings(settings)
        settings_id = str(uuid4())

        message_id = update_message(user_id=user.user_id, 
                                    status="started", 
                                    uploadcare_uris=uploadcare_uris, 
                                    message_id=None, 
                                    settings_id=settings_id, 
                                    s3_uris=None)

        workflow_json = generate_workflow(settings, image_ids, image_formats)

        # print(workflow_json)

        if workflow_json is None:
            update_message(user.user_id, message_id, "failed")
            raise HTTPException(status_code=500, detail="Error while processing the workflow.")
        
        url = f"{os.getenv('RUNPOD_DOMAIN')}/image-generation/"

        # Define the headers for the request
        headers = {
            'Content-Type': 'application/json'
        }

        # Define the payload for the request
        payload = {
            'workflow': workflow_json,
            'uploadcare_uris': uploadcare_uris,
            'image_ids': image_ids,
            'image_formats': image_formats,
            'message_id': message_id,
            'settings_id': settings_id,
            'user_id': user.user_id
        }

        background_tasks.add_task(send_post_request, url, headers, payload)
    else:
        raise HTTPException(status_code=403, detail="Upgrade your plan to unlock permissions.")
    
def get_batch(user: Account) -> Optional[Message]:
    return data.get_batch(user.user_id)