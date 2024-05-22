open_pose_dwp = {
  "208": {
    "inputs": {
      "strength": 1,
      "start_percent": 0,
      "end_percent": 1,
      "control_net": [
        "209",
        0
      ],
      "image": [
        "223",
        0
      ]
    },
    "class_type": "Control Net Stacker",
    "_meta": {
      "title": "Control Net Stacker"
    }
  },
  "209": {
    "inputs": {
      "control_net_name": "control_v11p_sd15_openpose_fp16.safetensors"
    },
    "class_type": "ControlNetLoader",
    "_meta": {
      "title": "Load ControlNet Model"
    }
  },
  "210": {
    "inputs": {
      "image": "image_2024-02-05_171328213.png",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "223": {
    "inputs": {
      "detect_hand": "enable",
      "detect_body": "enable",
      "detect_face": "enable",
      "resolution": 512,
      "bbox_detector": "yolox_l.onnx",
      "pose_estimator": "dw-ll_ucoco_384.onnx",
      "image": [
        "210",
        0
      ]
    },
    "class_type": "DWPreprocessor",
    "_meta": {
      "title": "DWPose Estimator"
    }
  },
}

canny = {
  "214": {
    "inputs": {
      "strength": 1,
      "start_percent": 0,
      "end_percent": 1,
      "control_net": [
        "215",
        0
      ],
      "image": [
        "241",
        0
      ]
    },
    "class_type": "Control Net Stacker",
    "_meta": {
      "title": "Control Net Stacker"
    }
  },
  "215": {
    "inputs": {
      "control_net_name": "control_v11p_sd15_canny_fp16.safetensors"
    },
    "class_type": "ControlNetLoader",
    "_meta": {
      "title": "Load ControlNet Model"
    }
  },
  "216": {
    "inputs": {
      "image": "00089-sRAW.png",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "241": {
    "inputs": {
      "low_threshold": 0.1,
      "high_threshold": 0.2,
      "image": [
        "216",
        0
      ]
    },
    "class_type": "Canny",
    "_meta": {
      "title": "Canny"
    }
  },
}

midas_depth_map = {
  "211": {
    "inputs": {
      "strength": 1,
      "start_percent": 0,
      "end_percent": 1,
      "control_net": [
        "212",
        0
      ],
      "image": [
        "321",
        0
      ]
    },
    "class_type": "Control Net Stacker",
    "_meta": {
      "title": "Control Net Stacker"
    }
  },
  "212": {
    "inputs": {
      "control_net_name": "control_v11f1p_sd15_depth_fp16.safetensors"
    },
    "class_type": "ControlNetLoader",
    "_meta": {
      "title": "Load ControlNet Model"
    }
  },
  "213": {
    "inputs": {
      "image": "image_2024-02-09_230918056.png",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "321": {
    "inputs": {
      "ckpt_name": "depth_anything_vitl14.pth",
      "resolution": 512,
      "image": [
        "213",
        0
      ]
    },
    "class_type": "DepthAnythingPreprocessor",
    "_meta": {
      "title": "Depth Anything"
    }
  },
}

ip2p = {
  "217": {
    "inputs": {
      "strength": 0.5,
      "start_percent": 0,
      "end_percent": 1,
      "control_net": [
        "220",
        0
      ],
      "image": [
        "218",
        0
      ]
    },
    "class_type": "Control Net Stacker",
    "_meta": {
      "title": "Control Net Stacker"
    }
  },
  "218": {
    "inputs": {
      "image": "image_2024-02-05_170026697.png",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "220": {
    "inputs": {
      "control_net_name": "control_v11e_sd15_ip2p_fp16.safetensors"
    },
    "class_type": "ControlNetLoader",
    "_meta": {
      "title": "Load ControlNet Model"
    }
  },
}

lora_stacker = {
  "207": {
    "inputs": {
      "input_mode": "simple",
      "lora_count": 1,
      "lora_name_1": "detail_slider_v4.safetensors",
      "lora_wt_1": 1.2,
      "model_str_1": 1,
      "clip_str_1": 1,
      "lora_name_2": "detail_slider_v4.safetensors",
      "lora_wt_2": 1.2,
      "model_str_2": 1,
      "clip_str_2": 1,
      "lora_name_3": "detail_slider_v4.safetensors",
      "lora_wt_3": 1.2,
      "model_str_3": 1,
      "clip_str_3": 1,
      "lora_name_4": "emotion_happy_slider_v1.safetensors",
      "lora_wt_4": 1.2,
      "model_str_4": 1,
      "clip_str_4": 1
    },
    "class_type": "LoRA Stacker",
    "_meta": {
      "title": "LoRA Stacker"
    }
  },
}

get_image_size = {
  "324": {
    "inputs": {
      "image": "image_2024-02-09_225707250.png",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "325": {
    "inputs": {
      "image": [
        "324",
        0
      ]
    },
    "class_type": "Get image size",
    "_meta": {
      "title": "Get image size"
    }
  },
}

random_prompts = {
  "222": {
    "inputs": {
      "text": "amateur candid phone selfie of a cute attractive 30 year old white girl with long blonde wavy hair, bedroom, day time indoors, looking at the camera, nice clothing, posted to snapchat story in 2021",
      "seed": 881,
      "autorefresh": "No"
    },
    "class_type": "DPRandomGenerator",
    "_meta": {
      "title": "Random Prompts"
    }
  },
}

image_size = {
  "326": {
    "inputs": {
      "Number": "512"
    },
    "class_type": "Int",
    "_meta": {
      "title": "Int"
    }
  },
  "327": {
    "inputs": {
      "Number": "768"
    },
    "class_type": "Int",
    "_meta": {
      "title": "Int"
    }
  },
}

ipa1 = {
  "278": {
    "inputs": {
      "weight": 1,
      "noise": 0,
      "weight_type": "original",
      "start_at": 0,
      "end_at": 1,
      "unfold_batch": False,
      "ipadapter": [
        "279",
        0
      ],
      "clip_vision": [
        "281",
        0
      ],
      "image": [
        "390",
        0
      ],
      "model": [
        "206",
        0
      ]
    },
    "class_type": "IPAdapterApply",
    "_meta": {
      "title": "Apply IPAdapter"
    }
  },
  "279": {
    "inputs": {
      "ipadapter_file": "ip-adapter-plus-face_sd15.bin"
    },
    "class_type": "IPAdapterModelLoader",
    "_meta": {
      "title": "Load IPAdapter Model"
    }
  },
  "281": {
    "inputs": {
      "clip_name": "model.safetensors"
    },
    "class_type": "CLIPVisionLoader",
    "_meta": {
      "title": "Load CLIP Vision"
    }
  },
  "390": {
    "inputs": {
      "image": "image_2024-03-19_145012816.png",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  }
}

efficient_loader = {
  "206": {
    "inputs": {
      "ckpt_name": "realisticVisionV51_v51VAE.safetensors",
      "vae_name": "Baked VAE",
      "clip_skip": -1,
      "lora_name": "None",
      "lora_model_strength": 1.2,
      "lora_clip_strength": 1,
      "negative": "earings, body rolls, holding phone, phone, phones, bokeh, (background blur:1.4), bokeh, (reflective skin:1.3), (glowing skin:1.5), nose piercing, (NSFW:1.5), (smooth skin:1.6), (disfigured iris:1.2), (bad eyes:1.4), phone, (holding phone:1.4),  cartoon, (3d:1.4), (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), (close up), strange colours, blurry, boring, sketch, lackluster, face portrait, signature, letters, watermark, grayscale\n",
      "token_normalization": "none",
      "weight_interpretation": "comfy",
      "empty_latent_width": [
        "326",
        0
      ],
      "empty_latent_height": [
        "327",
        0
      ],
      "batch_size": 4
    },
    "class_type": "Efficient Loader",
    "_meta": {
      "title": "Efficient Loader"
    }
  },
}

ksampler_efficient1 = {
  "229": {
    "inputs": {
      "seed": 874917062144626,
      "steps": 60,
      "cfg": 4,
      "sampler_name": "euler_ancestral",
      "scheduler": "normal",
      "denoise": 1,
      "preview_method": "auto",
      "vae_decode": "true",
      "model": [
        "206",
        0
      ],
      "positive": [
        "206",
        1
      ],
      "negative": [
        "206",
        2
      ],
      "latent_image": [
        "206",
        3
      ],
      "optional_vae": [
        "206",
        4
      ]
    },
    "class_type": "KSampler (Efficient)",
    "_meta": {
      "title": "KSampler (Efficient)"
    }
  },
}

preview_image1 = {
  "359": {
    "inputs": {
      "images": [
        "229",
        5
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "Preview Image"
    }
  },
}

ksampler_efficient2 = {
  "246": {
    "inputs": {
      "seed": 81516205459427,
      "steps": 40,
      "cfg": 4,
      "sampler_name": "dpmpp_sde_gpu",
      "scheduler": "normal",
      "denoise": 0.45,
      "preview_method": "auto",
      "vae_decode": "true",
      "model": [
        "229",
        0
      ],
      "positive": [
        "229",
        1
      ],
      "negative": [
        "229",
        2
      ],
      "latent_image": [
        "229",
        3
      ],
      "optional_vae": [
        "229",
        4
      ]
    },
    "class_type": "KSampler (Efficient)",
    "_meta": {
      "title": "KSampler (Efficient)"
    }
  },
}

preview_image2 = {
  "266": {
    "inputs": {
      "images": [
        "246",
        5
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "Preview Image"
    }
  },
}

ipa2 = {
  "251": {
    "inputs": {
      "ckpt_air": "{model_id}@{model_version}",
      "ckpt_name": "realisticVisionV51_v51VAE.safetensors",
      "download_chunks": 4,
      "download_path": "models\\checkpoints"
    },
    "class_type": "CivitAI_Checkpoint_Loader",
    "_meta": {
      "title": "Civitait Checkpoint Loader #2"
    }
  },
  "284": {
    "inputs": {
      "weight": 1,
      "noise": 1,
      "weight_type": "channel penalty",
      "start_at": 0,
      "end_at": 1,
      "unfold_batch": False,
      "ipadapter": [
        "285",
        0
      ],
      "clip_vision": [
        "287",
        0
      ],
      "image": [
        "390",
        0
      ],
      "model": [
        "251",
        0
      ]
    },
    "class_type": "IPAdapterApply",
    "_meta": {
      "title": "Apply IPAdapter"
    }
  },
  "285": {
    "inputs": {
      "ipadapter_file": "ip-adapter-plus-face_sd15.bin"
    },
    "class_type": "IPAdapterModelLoader",
    "_meta": {
      "title": "Load IPAdapter Model"
    }
  },
  "287": {
    "inputs": {
      "clip_name": "model.safetensors"
    },
    "class_type": "CLIPVisionLoader",
    "_meta": {
      "title": "Load CLIP Vision"
    }
  },
  "288": {
    "inputs": {
      "image": "images (2).jpg",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
}