import threading, socketserver, http.server, pytest
from alerting.notify_webhook_v1 import _post
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):self.send_response(200);self.end_headers();H.flag=True
    def log_message(self,*a):pass
H.flag=False
@pytest.fixture
def srv():
    with socketserver.TCPServer(("localhost",0),H) as s:
        t=threading.Thread(target=s.serve_forever);t.daemon=True;t.start()
        yield f"http://localhost:{s.server_address[1]}";s.shutdown();t.join()
def test_post_ok(srv):
    assert _post(srv,{"x":1})==200 and H.flag
