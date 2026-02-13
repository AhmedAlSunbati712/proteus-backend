from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from .config import Settings


@dataclass
class CatVTONModel:
    settings: Settings

    def __post_init__(self) -> None:
        self._model = None
        self._processor = None
        self._is_stub = self.settings.inference_backend == "stub"

    def load(self) -> None:
        if self._is_stub:
            return

        # Lazy import so local setup can run in stub mode without torch/catvton installed.
        # Replace this block with the exact CatVTON loading code you use.
        try:
            import torch  # type: ignore

            _ = torch
        except ImportError as exc:
            raise RuntimeError(
                "INFERENCE_BACKEND=catvton requires torch and CatVTON dependencies installed"
            ) from exc

        # TODO: initialize actual CatVTON model + preprocessors here.
        self._model = "loaded"

    def infer(self, person_img: Image.Image, outfit_img: Image.Image) -> Image.Image:
        if self._is_stub:
            return self._stub_infer(person_img, outfit_img)

        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        # TODO: Replace with true CatVTON inference.
        return self._stub_infer(person_img, outfit_img)

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
