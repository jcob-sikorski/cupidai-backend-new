from pydantic import BaseModel

from typing import List, Dict, Optional
from datetime import datetime


class Settings(BaseModel):
    # Basic settings (mandatory)
    basic_preset: str
    pos_prompt_enabled: bool
    basic_pos_text_prompt: str
    basic_neg_text_prompt: str
    basic_sampling_steps: int # max is 120
    basic_sampler_method: str # in samplers
    basic_model: str # in checkpoint models
    basic_width: int
    basic_height: int
    basic_cfg_scale: float  # max is 100.0
    basic_batch_size: int # range is 1-8
    basic_batch_count: int # range is 1-4
    basic_denoise: float # max is 1.0

    # IPA 1 settings (optional)
    ipa_1_enabled: bool = False
    ipa_1_model: Optional[str] = None # in ipa models
    ipa_1_reference_image: Optional[str] = None # uploadcare uri
    ipa_1_weight: Optional[float] = None # max is 1.0
    ipa_1_noise: Optional[float] = None  # max is 1.0
    ipa_1_weight_type: Optional[str] = None
    ipa_1_start_at: Optional[float] = None # max is 1.0
    ipa_1_end_at: Optional[float] = None # max is 1.0

    # IPA 2 settings (optional)
    ipa_2_enabled: bool = False
    ipa_2_model: Optional[str] = None # in ipa models
    ipa_2_reference_image: Optional[str] = None # uploadcare uri
    ipa_2_weight: Optional[float] = None # max is 1.0
    ipa_2_noise: Optional[float] = None  # max is 1.0
    ipa_2_weight_type: Optional[str] = None
    ipa_2_start_at: Optional[float] = None # max is 1.0
    ipa_2_end_at: Optional[float] = None # max is 1.0

    # Refinement settings (optional)
    refinement_enabled: bool = False
    refinement_seed: Optional[int] = None
    refinement_steps: Optional[int] = None # max is 120
    refinement_cfg_scale: Optional[float] = None # max is 100
    refinement_denoise: Optional[float] = None # max is 1.0
    refinement_sampler: Optional[str] = None # in sampler models

    # Lora settings (optional)
    lora_count: Optional[int] = None # range is 1-4
    lora_models: Optional[List[str]] = None # in lora models
    lora_strengths: Optional[List[float]] = None # max is 10.0
    lora_enabled: List[bool] = [False, False, False, False]

    civitai_enabled: bool = False
    civitai_model: Optional[str] = None # in checkpoint models

class Message(BaseModel):
    user_id: Optional[str] = None
    status: Optional[str] = None
    uploadcare_uris: Optional[List[str]] = None
    created_at: datetime | None = None
    message_id: Optional[str] = None
    settings_id: Optional[str] = None
    s3_uris: Optional[List[str]] = None
