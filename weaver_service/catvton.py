from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from PIL import Image
from huggingface_hub import snapshot_download

from .config import Settings


@dataclass
class CatVTONModel:
    settings: Settings

    def __post_init__(self) -> None:
        self._pipeline: Any | None = None
        self._resize_and_crop = None
        self._resize_and_padding = None
        self._torch: Any | None = None
        self._weight_dtype: Any | None = None
        self._is_stub = self.settings.inference_backend == "stub"

    def load(self) -> None:
        if self._is_stub:
            return

        try:
            import torch  # type: ignore
            from weaver_service.vendor.catvton.model.pipeline import CatVTONPix2PixPipeline  # type: ignore
            from weaver_service.vendor.catvton.utils import init_weight_dtype, resize_and_crop, resize_and_padding  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "INFERENCE_BACKEND=catvton requires torch + CatVTON source code vendored under "
                "`weaver_service/vendor/catvton` (model/pipeline.py and utils.py)."
            ) from exc

        if self.settings.allow_tf32 and torch.cuda.is_available():
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

        model_path = self._resolve_model_path()
        self._torch = torch
        self._weight_dtype = init_weight_dtype(self.settings.mixed_precision)
        self._resize_and_crop = resize_and_crop
        self._resize_and_padding = resize_and_padding
        self._pipeline = CatVTONPix2PixPipeline(
            base_ckpt=self.settings.catvton_base_model_path,
            attn_ckpt=model_path,
            attn_ckpt_version=self.settings.catvton_model_variant,
            weight_dtype=self._weight_dtype,
            use_tf32=self.settings.allow_tf32,
            device=self.settings.device,
            skip_safety_check=True,
        )

    def infer(self, person_img: Image.Image, outfit_img: Image.Image) -> Image.Image:
        if self._is_stub:
            return self._stub_infer(person_img, outfit_img)

        if self._pipeline is None or self._torch is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        person_image = person_img.convert("RGB")
        cloth_image = outfit_img.convert("RGB")
        person_image = self._resize_and_crop(person_image, (self.settings.width, self.settings.height))
        cloth_image = self._resize_and_padding(cloth_image, (self.settings.width, self.settings.height))

        generator = None
        if self.settings.seed >= 0:
            generator = self._torch.Generator(device=self.settings.device).manual_seed(self.settings.seed)

        result = self._pipeline(
            image=person_image,
            condition_image=cloth_image,
            num_inference_steps=self.settings.num_inference_steps,
            guidance_scale=self.settings.guidance_scale,
            generator=generator,
        )[0]
        return result.convert("RGBA")

    def _resolve_model_path(self) -> str:
        if os.path.isdir(self.settings.catvton_model_dir):
            return self.settings.catvton_model_dir
        return snapshot_download(repo_id=self.settings.catvton_model_id)

    @staticmethod
    def _stub_infer(person_img: Image.Image, outfit_img: Image.Image) -> Image.Image:
        """
        Development fallback: alpha-composite resized outfit over the person's torso area.
        Lets you validate end-to-end queue/event/S3 flow before full model integration.
        """
        base = person_img.convert("RGBA")
        overlay = outfit_img.convert("RGBA")

        bw, bh = base.size
        target_w = int(bw * 0.6)
        target_h = int(bh * 0.55)
        overlay = overlay.resize((max(target_w, 1), max(target_h, 1)))

        x = int((bw - overlay.width) / 2)
        y = int(bh * 0.2)

        canvas = base.copy()
        canvas.alpha_composite(overlay, dest=(x, y))
        return canvas
