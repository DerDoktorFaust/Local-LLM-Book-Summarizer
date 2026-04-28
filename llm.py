import gc

import mlx.core as mx
from mlx_lm import load, generate


MODEL_PATH = "/Users/cgoodwin/.lmstudio/models/mlx-community/gemma-3-12b-it-qat-4bit"

MAX_TOKENS = 2048

_model = None
_tokenizer = None


def load_model():
    global _model, _tokenizer

    if _model is None or _tokenizer is None:
        print("Loading model...")
        _model, _tokenizer = load(MODEL_PATH)
        print("Model loaded.")

    return _model, _tokenizer


def unload_model():
    global _model, _tokenizer

    if _model is not None or _tokenizer is not None:
        print("Unloading model...")

    _model = None
    _tokenizer = None

    gc.collect()
    mx.clear_cache()

    print("Model unloaded.")


def generate_text(prompt: str, max_tokens: int = MAX_TOKENS) -> str:
    model, tokenizer = load_model()

    response = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        verbose=False,
    )

    if hasattr(response, "text"):
        text = response.text
    elif hasattr(response, "output"):
        text = response.output
    else:
        text = str(response)

    return text.strip()