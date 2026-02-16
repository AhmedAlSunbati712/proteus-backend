from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import snapshot_download


def main() -> None:
    repo_id = os.getenv("CATVTON_REPO_ID", "zhengchong/CatVTON-MaskFree")
    variant = os.getenv("CATVTON_MODEL_VARIANT", "mix-48k-1024")
    target_dir = os.getenv("CATVTON_MODEL_DIR", "weaver_service/models/CatVTON-MaskFree")
    download_full_repo = os.getenv("CATVTON_DOWNLOAD_FULL_REPO", "false").lower() == "true"

    Path(target_dir).mkdir(parents=True, exist_ok=True)

    allow_patterns = None
    if not download_full_repo:
        allow_patterns = [
            f"{variant}/attention/model.safetensors",
            "config.json",
        ]

    local_path = snapshot_download(
        repo_id=repo_id,
        local_dir=target_dir,
        allow_patterns=allow_patterns,
        local_dir_use_symlinks=False,
    )

    print(f"Downloaded model snapshot to: {local_path}")


if __name__ == "__main__":
    main()
