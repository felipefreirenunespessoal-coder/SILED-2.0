"""Compatibilidade com hospedagens que esperam app:app."""
from siled import create_app

app = create_app()

if __name__ == "__main__":
    from main import main
    main()
