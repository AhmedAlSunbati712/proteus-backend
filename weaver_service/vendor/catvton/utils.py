from __future__ import annotations

from typing import Iterable

import numpy as np
import torch
from PIL import Image
from diffusers.image_processor import VaeImageProcessor


def init_weight_dtype(mixed_precision: str) -> torch.dtype:
    return {
        "no": torch.float32,
        "fp16": torch.float16,
        "bf16": torch.bfloat16,
    }[mixed_precision]


def resize_and_crop(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = image.resize((int(src_w * scale), int(src_h * scale)), Image.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def resize_and_padding(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = image.size
    scale = min(target_w / src_w, target_h / src_h)
    resized = image.resize((int(src_w * scale), int(src_h * scale)), Image.LANCZOS)
    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    x = (target_w - resized.width) // 2
    y = (target_h - resized.height) // 2
    canvas.paste(resized, (x, y))
    return canvas


def prepare_image(image: Image.Image | torch.Tensor) -> torch.Tensor:
    if isinstance(image, torch.Tensor):
        if image.ndim == 3:
            image = image.unsqueeze(0)
        return image

    processor = VaeImageProcessor(vae_scale_factor=8)
    return processor.preprocess(image)


def prepare_mask_image(mask: Image.Image | torch.Tensor) -> torch.Tensor:
    if isinstance(mask, torch.Tensor):
        if mask.ndim == 3:
            mask = mask.unsqueeze(0)
        return mask

    processor = VaeImageProcessor(
        vae_scale_factor=8,
        do_normalize=False,
        do_binarize=True,
        do_convert_grayscale=True,
    )
    return processor.preprocess(mask)


def compute_vae_encodings(images: torch.Tensor, vae) -> torch.Tensor:
    images = images.to(device=vae.device, dtype=vae.dtype)
    posterior = vae.encode(images).latent_dist
    latents = posterior.sample()
    return latents * vae.config.scaling_factor


def numpy_to_pil(images: np.ndarray | Iterable[np.ndarray]) -> list[Image.Image]:
    if isinstance(images, np.ndarray) and images.ndim == 3:
        images = images[None, ...]
    pil_images = []
    for image in images:
        if image.ndim == 3 and image.shape[-1] == 1:
            pil_images.append(Image.fromarray(image.squeeze().astype("uint8"), mode="L"))
        else:
            pil_images.append(Image.fromarray(image.astype("uint8")))
    return pil_images
