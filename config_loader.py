from pathlib import Path
import yaml


CONFIG_PATH = Path("config.yaml")


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "config.yaml not found. Please create it and set your model_path."
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if "model_path" not in config or not config["model_path"]:
        raise ValueError("config.yaml must contain a valid 'model_path'.")

    return config