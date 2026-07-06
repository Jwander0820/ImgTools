from imgtools.ui.server import serve


HOST = "127.0.0.1"
PORT = 8765


def main():
    """
    Start the ImgTools local UI.

    PyCharm usage:
        Run this file directly, then use http://127.0.0.1:8765.
    """
    serve(HOST, PORT, open_browser=True)


if __name__ == "__main__":
    main()

