# Weaver Service

## Download CatVTON-MaskFree Model

Run these commands from the repository root (`proteus-backend`).

1. Create and activate a Python 3.10+ virtual environment:

```bash
python3.10 -m venv .venv-weaver
source .venv-weaver/bin/activate
```

2. Install Weaver dependencies:

```bash
pip install --upgrade pip
pip install -r weaver_service/requirements.txt
```

3. (Optional) copy local env config:

```bash
cp weaver_service/.env.example weaver_service/.env
```

4. Download model weights:

```bash
python weaver_service/download_model.py
```

By default, this downloads:
- `mix-48k-1024/attention/model.safetensors`
- `config.json`

into:
- `weaver_service/models/CatVTON-MaskFree`

## Useful Environment Variables

- `CATVTON_REPO_ID` (default: `zhengchong/CatVTON-MaskFree`)
- `CATVTON_MODEL_VARIANT` (default: `mix-48k-1024`)
- `CATVTON_MODEL_DIR` (default: `weaver_service/models/CatVTON-MaskFree`)
- `CATVTON_DOWNLOAD_FULL_REPO` (`true` or `false`, default: `false`)

Example (download full repo files):

```bash
CATVTON_DOWNLOAD_FULL_REPO=true python weaver_service/download_model.py
```
