from typing import Optional
import json
import os
from model.image_generation import Settings


def set_basic_settings(workflow, settings, reference_image_path):
    print("Setting basic settings")

    for node in workflow.get('nodes', []):
        node_id = node.get('id')
        if node_id == 206:
            print("Setting values for node 206")
            node['widgets_values'][0] = settings.model
            node['widgets_values'][10] = int(settings.width)
            node['widgets_values'][11] = int(settings.height)
            node['widgets_values'][12] = int(settings.n_images)
        elif node_id == 222:
            node['widgets_values'][0] = settings.pos_prompt
        elif node_id == 229:
            print(f"Setting sampling steps for node {node_id}")
            node['widgets_values'][2] = int(settings.sampling_steps)
        elif node_id == 280:
            print("Setting reference image path for node 280")
            node['widgets_values'][0] = reference_image_path


def set_controlnet_parameters(workflow, 
                              settings, 
                              controlnet_reference_image_path, 
                              image_loader_id, 
                              controlnet_stacker_id):
    print("Setting controlnet parameters")
    for node in workflow.get('nodes', []):
        node_id = node.get('id')
        if node_id == int(image_loader_id):
            print(f"Setting controlnet reference image path for node {image_loader_id}")
            node['widgets_values'][0] = controlnet_reference_image_path
        elif node_id == int(controlnet_stacker_id):
            print(f"Setting controlnet stacker values for node {controlnet_stacker_id}")
            node['widgets_values'][0] = float(settings.controlnet_strength)/100
            node['widgets_values'][1] = float(settings.controlnet_start_percent)/100
            node['widgets_values'][2] = float(settings.controlnet_end_percent)/100


def set_controlnet(workflow, settings, controlnet_reference_image_path):
    if settings.controlnet_enabled:
        print("Controlnet is enabled")
        link_map = {
            "Pose": (208, 210, 222),
            "Depth": (211, 213, 221),
            "Edge Detection": (214, 216, 220),
            "Resolution Enhancement": (217, 218, 219)
        }
        
        if settings.controlnet_model in link_map:
            controlnet_stacker_id, image_loader_id, link_id = link_map[settings.controlnet_model]

            print("CONTROLNET STACKER ID: ", controlnet_stacker_id)
            print("IMAGE LOADER ID: ", image_loader_id)
            print("LINK ID: ", link_id)

            set_controlnet_parameters(workflow, 
                                      settings, 
                                      controlnet_reference_image_path, 
                                      image_loader_id, 
                                      controlnet_stacker_id)
            
            print("WORFKLOW LAST LINK ID BEFORE: ", workflow['last_link_id'])
            workflow['last_link_id'] = link_id
            print("WORFKLOW LAST LINK ID AFTER: ", workflow['last_link_id'])

            for node in workflow.get('nodes', []):
                if node.get('id') == controlnet_stacker_id:
                    print("WORFKLOW CONTROLNET STACKER OUTPUTS BEFORE: ", node['outputs'])
                    print(f"Setting controlnet link for node {controlnet_stacker_id}")
                    node['outputs'][0]['links'] = [link_id]
                    print("WORFKLOW CONTROLNET STACKER OUTPUTS AFTER: ", node['outputs'])
                    break


            for node in workflow.get('nodes', []):
                if node.get('id') == 206:
                    print("WORFKLOW KSAMPLER EFFICIENT INPUTS BEFORE: ", node['inputs'])
                    print("Setting controlnet link for node 206")
                    node['inputs'].append({
                            "name": "cnet_stack",
                            "type": "CONTROL_NET_STACK",
                            "link": link_id,
                            "slot_index": 1
                        }
                    )
                    print("WORFKLOW KSAMPLER EFFICIENT INPUTS AFTER: ", node['inputs'])
                    break
            
            print("WORFKLOW LINKS BEFORE: ", workflow['links'])
            workflow['links'].append([
                  link_id,
                  controlnet_stacker_id,
                  0,
                  206,
                  1,
                  "CONTROL_NET_STACK"
                ]
            )
            print("WORFKLOW LINKS AFTER: ", workflow['links'])


def generate_workflow(settings: Settings, reference_image_path, controlnet_reference_image_path) -> Optional[dict]:
    try:
        with open('./comfyui/workflow.json', 'r') as file:
            workflow = json.load(file)

        set_basic_settings(workflow, settings, reference_image_path)
        set_controlnet(workflow, settings, controlnet_reference_image_path)

        return workflow

    except Exception as e:
        print(f"AN ERROR OCCURRED DURING WORKFLOW EXECUTION: {str(e)}")
        return None
