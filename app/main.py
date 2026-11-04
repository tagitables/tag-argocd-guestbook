from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from html import escape

entries = []

class GuestbookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        items = "".join(
            f"<li>{escape(entry)}</li>" for entry in entries
        )

        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Tag Guestbook</title></head>
        <body>
            <h1>Tag Guestbook</h1>
            <p>Deployed using ArgoCD GitOps on AWS EKS ARM64.</p>
            <form method="POST">
                <input name="message" placeholder="Leave a message" required>
                <button type="submit">Sign Guestbook</button>
            </form>
            <h2>Messages</h2>
            <ul>{items}</ul>
        </body>
        </html>
        """

        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 4096:
            self.send_error(413)
            return

        data = self.rfile.read(length).decode()
        message = parse_qs(data).get("message", [""])[0].strip()

        if message:
            entries.append(message)

        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

HTTPServer(("0.0.0.0", 80), GuestbookHandler).serve_forever()
