from typing import List, Optional

import importlib

import os

from model.image_generation import Settings

class ModelInterface():
    def __init__(self):
        self.lora_stacker = self.load_json("lora_stacker")
        self.image_size = self.load_json("image_size")
        self.get_image_size = self.load_json("get_image_size")
        self.random_prompts = self.load_json("random_prompts")
        self.ipa1 = self.load_json("ipa1")
        self.ipa2 = self.load_json("ipa2")
        self.efficient_loader = self.load_json("efficient_loader")
        self.ksampler_efficient1 = self.load_json("ksampler_efficient1")
        self.ksampler_efficient2 = self.load_json("ksampler_efficient2")
        self.preview_image1 = self.load_json("preview_image1")
        self.preview_image2 = self.load_json("preview_image2")

        self.used_components = set()

    def load_json(self, 
                  unit_name: str):
        # Import the JSON dictionary directly without decoding
        try:
            # Assuming all JSON data is stored in the JSONEngine module
            module = importlib.import_module("comfyui.JSONEngine")
            json_dict = getattr(module, unit_name)
            # Directly return the dictionary without json.loads
            return json_dict
        except (ImportError, AttributeError) as e:
            print(f"Error processing unit {unit_name}: {str(e)}")
            return None

    def finalize(self):
        # Initialize an empty dictionary to hold the combined data
        combined_json = {}
        # Iterate through each used component
        for component in self.used_components:
            # print(component)
            component_data = getattr(self, component, None)
            # print(component_data)
            if isinstance(component_data, dict):
                # Merge the component's values into the combined_json
                for key, value in component_data.items():
                    combined_json[key] = value

        # Sort keys that are integer strings in ascending order
        combined_json_sorted = {}
        sorted_keys = sorted(combined_json.keys(), key=lambda x: int(x) if x.isdigit() else x)
        for key in sorted_keys:
            combined_json_sorted[key] = combined_json[key]

        return combined_json_sorted


    def choose_output_size(self, 
                           int1: int, 
                           int2: int, 
                           image_path: str = ""):
        """
        ################# CHOOSE OUTPUT SIZE #################
        (Optional) Choose image for size reference
        1. Set the output image size
        2. Connect the int1 to empty_latent_width in efficient loader
        3. Connect the int2 to empty_latent_height in efficient loader
        
        (Default) Choose height and width of the output image
        1. Set the int1 to empty_latent_width in efficient loader
        2. Connect the int2 to empty_latent_height in efficient loader
        """

        # set the output image size
        if image_path:
            self.used_components.discard("image_size")
            self.get_image_size["324"]["inputs"]["image"] = image_path
            self.used_components.add("get_image_size")
        else:
            self.used_components.discard("get_image_size")
            self.image_size["326"]["inputs"]["Number"] = int1
            self.image_size["327"]["inputs"]["Number"] = int2
            self.used_components.add("image_size")

        # Connect the int1, int2 to empty_latent_width/height in efficient loader
            
        self.efficient_loader["206"]["inputs"]["empty_latent_width"][0] = "325" if image_path else "326"
        self.efficient_loader["206"]["inputs"]["empty_latent_width"][1] = 0
    
        self.efficient_loader["206"]["inputs"]["empty_latent_height"][0] = "325" if image_path else "327"
        self.efficient_loader["206"]["inputs"]["empty_latent_height"][1] = 1 if image_path else 0

    def connect_lora(self, 
                     count: int, 
                     models: List[str], 
                     strengths: List[str], 
                     enabled: List[bool]):
        """
        ################# CONNECT LORA #################
        (Optional) Connect lora to Efficient Loader
        1. Connect lora to lora_stack in Efficient Loader
        """
        # Connect Lora to the lora_stack in efficient loader
        self.lora_stacker["207"]["inputs"]["lora_count"] = count

        for i in range(count):  # Assuming 'enabled' has 4 elements.
            if enabled[i]:
                index = i + 1
                self.lora_stacker["207"]["inputs"][f"lora_name_{index}"] = models[i]
                self.lora_stacker["207"]["inputs"][f"model_str_{index}"] = strengths[i]

        self.used_components.add("lora_stacker")

    def connect_random_prompts(self, 
                               positive_prompt: str):
        """
        ################# CONNECT RANDOM PROMPTS #################
        (Optional) Connect random prompts to the efficient loader
        1. Set the prompt
        2. Connect random prompts to the efficient loader as positive
        """
        # Set the pos prompt
        self.random_prompts["222"]["inputs"]["text"] = positive_prompt
        self.used_components.add("random_prompts")

    def connect_efficient_loader(self, 
                                ckpt_name: str, 
                                negative_prompt: str, 
                                batch_size: int,
                                lora_enabled: List[bool],
                                random_prompts_enabled: bool = True):
        """
        ################# SET UP EFFICIENT LOADER #################
        (Default) Provide a configuration for the efficient loader
        1. Set the model
        2. Set the negative prompt
        3. (Optional) connect model to ApplyIpAdapter1
        4. (Default) connect model to model in KSamplerEfficient1
        """

        # Set the ckpt_name in efficient loader
        self.efficient_loader["206"]["inputs"]["ckpt_name"] = ckpt_name

        # Set the negative prompt in efficient loader
        self.efficient_loader["206"]["inputs"]["negative"] = negative_prompt

       # Set the batch size in efficient loader
        self.efficient_loader["206"]["inputs"]["batch_size"] = batch_size

        self.used_components.add("efficient_loader")

        if random_prompts_enabled:
            self.efficient_loader["206"]["inputs"]["positive"] = ["222", 0]

        print(f"LORA ENABLED: {lora_enabled}")
        if sum(lora_enabled) > 0:
            self.efficient_loader["206"]["inputs"]["lora_stack"] = ["207", 0]

    def connect_ksampler_efficient1(self,
                                    steps: int, 
                                    cfg_scale: float, 
                                    denoise: float, 
                                    sampler: str, 
                                    ipa1_enabled: bool = False):
        """
        ################# CONNECT KSAMPLER EFFICENT 2 #################
        """
        # self.ksampler_efficient1["229"]["inputs"]["seed"] = seed
        self.ksampler_efficient1["229"]["inputs"]["steps"] = steps
        self.ksampler_efficient1["229"]["inputs"]["cfg"] = cfg_scale
        self.ksampler_efficient1["229"]["inputs"]["denoise"] = denoise
        self.ksampler_efficient1["229"]["inputs"]["sampler_name"] = sampler

        self.used_components.add("ksampler_efficient1")

        if ipa1_enabled:
            self.ksampler_efficient1["229"]["inputs"]["model"] = ["278", 0]
        else:
            self.ksampler_efficient1["229"]["inputs"]["model"] = ["206", 0]
            


    def connect_ip_adapter_1(self, 
                             image_path: str, 
                             model: str, 
                             weight: int = 1, 
                             noise: int = 0, 
                             weight_type: str = "original", 
                             start_at: int = 0, 
                             end_at: int = 1):
        """
        ################# CONNECT IP ADAPTER 1 #################
        (Optional) Provide configuration for ip adapter 1, connect it to the KSamplerEfficient
        1. Set the image path for both (or the first one only) adapters
        2. Set the model for load ipadapter model
        3. (Optional) set weight, set noise, set weight_type, set start_at, set end_at
        4. Disconnect efficient loader model from ksamplerefficient, connect the 
        efficient loader’s model to apply adapter model and connect apply adapter
        model to ksamplerefficient model
        """
        # set the image path
        self.ipa1["390"]["inputs"]["image"] = image_path

        # set parameters
        self.ipa1["278"]["inputs"]["weight"] = weight
        self.ipa1["278"]["inputs"]["noise"] = noise
        self.ipa1["278"]["inputs"]["weight_type"] = weight_type
        self.ipa1["278"]["inputs"]["start_at"] = start_at
        self.ipa1["278"]["inputs"]["end_at"] = end_at

        self.ipa1["279"]["inputs"]["ipadapter_file"] = model

        self.used_components.add("ipa1")

    def connect_ksampler_efficient2(self, 
                                    seed: int, 
                                    steps: int, 
                                    cfg_scale: float, 
                                    denoise: float, 
                                    sampler: str, 
                                    ipa2_enabled: bool = True):
        """
        ################# CONNECT KSAMPLER EFFICENT 2 #################
        """

        self.ksampler_efficient2["246"]["inputs"]["seed"] = seed
        self.ksampler_efficient2["246"]["inputs"]["steps"] = steps
        self.ksampler_efficient2["246"]["inputs"]["cfg"] = cfg_scale
        self.ksampler_efficient2["246"]["inputs"]["denoise"] = denoise
        self.ksampler_efficient2["246"]["inputs"]["sampler_name"] = sampler

        self.used_components.add("ksampler_efficient2")

        if ipa2_enabled:
            self.ksampler_efficient2["246"]["inputs"]["model"] = ["284", 0]
        else:
            self.ksampler_efficient2["246"]["inputs"]["model"] = ["229", 0]

    def connect_ip_adapter_2(self, 
                             image_path: str, 
                             ipa_model: str, 
                             civitai_model: str = "", 
                             weight: int = 1, 
                             noise: int = 0, 
                             weight_type: str = "original", 
                             start_at: int = 0, 
                             end_at: int = 1,
                             civitai_enabled: bool = False):
        """
        ################# CONNECT IP ADAPTER 2 #################
        (Optional) Provide configuration for ip adapter 2, connect it to the KSamplerEfficient
        1. (Optional) Set the second image path for the second one only adapter - disconnect the first image loader from apply ip adapter and connect the second one
        2. Set the model for load ipadapter model
        3. (Optional) set weight, set noise, set weight_type, set start_at, set end_at
        4. Set the civitai model
        5. Disconnect ksamplerefficient1 model entirely from ksamplerefficient2 model, connect the  applyipadapter2 model to ksamplerefficient model
        """
        if image_path:
            # set the image path for the second image loader
            self.ipa2["288"]["inputs"]["image"] = image_path

            # disconnect the first image loader from apply ip adapter and connect the second one
            self.ipa2["284"]["inputs"]["image"] = ["288", 0]
        else:
            # disconnect the second image loader from apply ip adapter and connect the first one
            self.ipa2["284"]["inputs"]["image"] = ["390", 0]

        self.ipa2["285"]["inputs"]["ipadapter_file"] = ipa_model
        
        # set parameters
        self.ipa2["284"]["inputs"]["weight"] = weight
        self.ipa2["284"]["inputs"]["noise"] = noise
        self.ipa2["284"]["inputs"]["weight_type"] = weight_type
        self.ipa2["284"]["inputs"]["start_at"] = start_at
        self.ipa2["284"]["inputs"]["end_at"] = end_at

        self.used_components.add("ipa2")

        # if civitai_enabled:
        #     self.ipa2["251"]["inputs"]["ckpt_name"] = civitai_model

        #     self.ipa2["284"]["inputs"]["model"] = ["251", 0]
        # else:
        #     self.ipa2["284"]["inputs"]["model"] = ["229", 0]

def generate_workflow(settings: Settings, 
                      image_ids: List[str], 
                      image_formats: List[str]) -> Optional[dict]:
    try:
        print("INITIALIZING MODEL INTERFACE")
        model_interface = ModelInterface()

        predefined_path = os.getenv('COMFYUI_PREDEFINED_PATH')

        format_map = {"jpeg": ".jpeg",
                      "heic": ".heic",
                      "png": ".png"}

        print("CHOOSING OUTPUT SIZE")
        model_interface.choose_output_size(int1=settings.basic_width, 
                                           int2=settings.basic_height)

        if sum(settings.lora_enabled) > 0:
            print("CONNECTING LORA")
            model_interface.connect_lora(count=settings.lora_count, 
                                         models=settings.lora_models, 
                                         strengths=settings.lora_strengths, 
                                         enabled=settings.lora_enabled)

        if settings.pos_prompt_enabled:
            print("CONNECTING RANDOM PROMPTS")
            model_interface.connect_random_prompts(positive_prompt=settings.basic_pos_text_prompt)

        print("CONNECTING EFFICIENT LOADER")
        model_interface.connect_efficient_loader(ckpt_name=settings.basic_model,
                                                 negative_prompt=settings.basic_neg_text_prompt,
                                                 batch_size=settings.basic_batch_size,
                                                 lora_enabled=settings.lora_enabled,
                                                 random_prompts_enabled=settings.pos_prompt_enabled)
        
        if settings.ipa_1_enabled:
            print("CONNECTING IPA 1")

            file_extension = format_map[image_formats[0]]
            settings.ipa_1_reference_image = predefined_path + "/" + image_ids[0] + file_extension

            model_interface.connect_ip_adapter_1(image_path=settings.ipa_1_reference_image,
                                                 model=settings.ipa_1_model,
                                                 weight=settings.ipa_1_weight,
                                                 noise=settings.ipa_1_noise,
                                                 weight_type=settings.ipa_1_weight_type,
                                                 start_at=settings.ipa_1_start_at,
                                                 end_at=settings.ipa_1_end_at)
            

        model_interface.connect_ksampler_efficient1(steps=settings.basic_sampling_steps,
                                                    cfg_scale=settings.basic_cfg_scale,
                                                    denoise=settings.basic_denoise,
                                                    sampler=settings.basic_sampler_method,
                                                    ipa1_enabled=settings.ipa_1_enabled)
        
        if settings.refinement_enabled:
            if settings.ipa_2_enabled:
                if settings.ipa_2_reference_image:
                    file_extension = format_map[image_formats[1]]
                    settings.ipa_2_reference_image = predefined_path + "/" + image_ids[1] + file_extension

                model_interface.connect_ip_adapter_2(image_path=settings.ipa_2_reference_image,
                                                     ipa_model=settings.ipa_2_model,
                                                     civitai_model=settings.civitai_model,
                                                     weight=settings.ipa_2_weight,
                                                     noise=settings.ipa_2_noise,
                                                     weight_type=settings.ipa_2_weight_type,
                                                     start_at=settings.ipa_2_start_at,
                                                     end_at=settings.ipa_2_end_at,
                                                     civitai_enabled=settings.civitai_enabled)

            model_interface.connect_ksampler_efficient2(seed=settings.refinement_seed,
                                                        steps=settings.refinement_steps,
                                                        cfg_scale=settings.refinement_cfg_scale,
                                                        denoise=settings.refinement_denoise,
                                                        sampler=settings.refinement_sampler,
                                                        ipa2_enabled=settings.ipa_2_enabled)

        final_json = model_interface.finalize()

        return final_json

    except Exception as e:
        print(f"AN ERROR OCCURRED DURING WORKFLOW EXECUTION: {str(e)}")
        return None
