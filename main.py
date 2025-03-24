import json
import mimetypes
from pathlib import Path
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent
STATIC_DIR = Path(BASE_DIR) / "static"
jinja = Environment(loader=FileSystemLoader("templates"))


class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        templates_path = "templates/"
        match route.path:
            case "/":
                self.send_html(f"{templates_path}index.html")
            case "/read":
                self.render_template("read.jinja")
            case "/message":
                self.send_html(f"{templates_path}message.html")
            case _:
                file = search_file(STATIC_DIR, route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html(f"{templates_path}error.html", 404)

    def do_POST(self):
        size = self.headers.get("Content-Length")
        body = self.rfile.read(int(size)).decode("utf-8")
        parse_body = urllib.parse.unquote_plus(body)
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        data_dict = {
            key: value
            for key, value in [el.split("=") for el in parse_body.split("&")]
            if key and value
        }
        if data_dict:
            with open("storage/data.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                data.update({time: data_dict})
            with open("storage/data.json", "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
        self.send_response(302)
        self.send_header("Location", "/read")
        self.end_headers()

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status=200):
        self.send_response(status)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-type", mime_type)
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def render_template(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        with open("storage/data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            template = jinja.get_template(filename)
            content = template.render(messages=data)
            self.wfile.write(content.encode())


def search_file(path: Path, filename: str):
    for element in path.iterdir():
        if element.is_dir():
            result = search_file(element, filename)
            if result:
                return result
        elif element.name == filename:
            return element


def run(server_class=HTTPServer, handler_class=MyHandler):

    server_address = ("", 3000)
    httpd = server_class(server_address, handler_class)
    print("Server started on port - 3000")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server is shutting down...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run()
