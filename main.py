import sys


def main() -> int:
    try:
        from game import Game
    except ModuleNotFoundError as e:
        if e.name == "pygame":
            print(
                "Dépendance manquante: pygame\n\n"
                "Installe-la puis relance:\n"
                "  python -m pip install -r requirements.txt\n\n"
                "Ensuite:\n"
                "  python project/main.py"
            )
            return 1
        raise

    game = Game()
    return game.run()


if __name__ == "__main__":
    raise SystemExit(main())

