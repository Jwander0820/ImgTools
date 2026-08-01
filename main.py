"""Convenience entry point for launching the ImgTools local UI."""

from imgtools.ui.server import serve


HOST = "127.0.0.1"
PORT = 8765


def main() -> None:
    serve(HOST, PORT, open_browser=True)


if __name__ == "__main__":
    main()
