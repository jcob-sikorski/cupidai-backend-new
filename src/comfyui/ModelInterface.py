from typing import Optional
import json
import os
from model.image_generation import Settings


def set_basic_settings(workflow, settings, reference_image_path):
    print("Setting basic settings")
    
    workflow["206"]['inputs']['ckpt_name'] = settings.model        
    workflow["206"]['inputs']['empty_latent_width'] = int(settings.width)            
    workflow["206"]['inputs']['empty_latent_height'] = int(settings.height)    
    workflow["206"]['inputs']['batch_size'] = int(settings.n_images)

    workflow["222"]['inputs']['text'] = settings.pos_prompt

    workflow["229"]['inputs']['steps'] = int(settings.sampling_steps)

    workflow["280"]['inputs']['image'] = reference_image_path


def set_controlnet_parameters(workflow, 
                              settings, 
                              controlnet_reference_image_path, 
                              image_loader_id, 
                              controlnet_stacker_id):
    
    workflow[str(image_loader_id)]['inputs']['image'] = controlnet_reference_image_path

    workflow[str(controlnet_stacker_id)]['inputs']['strength'] = float(settings.controlnet_strength)/10
    workflow[str(controlnet_stacker_id)]['inputs']['start_percent'] = float(settings.controlnet_start_percent)/100
    workflow[str(controlnet_stacker_id)]['inputs']['end_percent'] = float(settings.controlnet_end_percent)/100


def set_controlnet(workflow, settings, controlnet_reference_image_path):
    if settings.controlnet_enabled:
        print("Controlnet is enabled")
        link_map = {
            "Pose": (208, 210),
            "Depth": (211, 213),
            "Edge Detection": (214, 216),
            "Resolution Enhancement": (217, 218)
        }
        
        if settings.controlnet_model in link_map:
            controlnet_stacker_id, image_loader_id = link_map[settings.controlnet_model]

            print("CONTROLNET STACKER ID: ", controlnet_stacker_id)
            print("IMAGE LOADER ID: ", image_loader_id)

            set_controlnet_parameters(workflow, 
                                      settings, 
                                      controlnet_reference_image_path, 
                                      image_loader_id, 
                                      controlnet_stacker_id)


            workflow['206']['inputs']['cnet_stack'] = [
              str(controlnet_stacker_id),
              0
            ]


def generate_workflow(settings: Settings, reference_image_path, controlnet_reference_image_path) -> Optional[dict]:
    try:
        with open('./comfyui/workflow_api.json', 'r') as file:
            workflow = json.load(file)

        set_basic_settings(workflow, settings, reference_image_path)
        set_controlnet(workflow, settings, controlnet_reference_image_path)

        return workflow

    except Exception as e:
        print(f"AN ERROR OCCURRED DURING WORKFLOW EXECUTION: {str(e)}")
        return None
