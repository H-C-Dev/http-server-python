import os
from pathlib import Path

def env_loader(filename=".env", search_from: str | Path | None = None) -> None:

    if search_from is None:
        import inspect
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        if module and hasattr(module, "__file__"):
            search_from = Path(module.__file__).resolve().parent
        else:
            search_from = Path.cwd()

    env_path = Path(search_from) / filename

    if not env_path.exists():
        raise FileNotFoundError(f".env not found at {env_path}")

    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            os.environ[key] = value