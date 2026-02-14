from __future__ import annotations

from dotenv import find_dotenv, load_dotenv

# Ensure .env is loaded from project root/current working directory.
load_dotenv(dotenv_path=find_dotenv(".env", usecwd=True), override=True)

from app.main import main


if __name__ == "__main__":
    main()
