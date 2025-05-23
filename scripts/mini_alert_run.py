import sys, pathlib, http.server, socketserver, threading
sys.path.append(pathlib.Path(__file__).resolve().parents[1].as_posix())
from alerting.notify_webhook_v1 import _post
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):self.send_response(200);self.end_headers()
    def log_message(self,*a):pass
with socketserver.TCPServer(("localhost",0),H) as s:
    t=threading.Thread(target=s.serve_forever);t.daemon=True;t.start()
    url=f"http://localhost:{s.server_address[1]}";print("Status",_post(url,{"text":"Hi"}))
    s.shutdown();t.join()
