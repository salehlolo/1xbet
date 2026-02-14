from __future__ import annotations

from dotenv import load_dotenv

# Ensure .env is loaded even when running this file directly.
load_dotenv()

from app.main import main


if __name__ == "__main__":
    main()
