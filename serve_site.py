"""
HTTP server for static site with regeneration endpoint
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import subprocess
import json
import os
from pathlib import Path


class AnalysisHandler(SimpleHTTPRequestHandler):
    """HTTP handler with regenerate endpoint"""

    def __init__(self, *args, **kwargs):
        # Set directory to static_site for serving
        super().__init__(*args, directory='static_site', **kwargs)

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/regenerate':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            try:
                print("\n🔄 Regenerating analysis...")

                # Run generate_site.py
                result = subprocess.run(
                    ['python', 'generate_site.py'],
                    check=True,
                    capture_output=True,
                    text=True
                )

                print(result.stdout)

                response = {
                    'status': 'success',
                    'message': 'Analysis regenerated successfully'
                }
                print("✅ Regeneration complete\n")

            except subprocess.CalledProcessError as e:
                print(f"❌ Regeneration failed: {e}\n")
                response = {
                    'status': 'error',
                    'message': f'Regeneration failed: {e.stderr}'
                }

            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        """Override to reduce noise in logs"""
        # Only log errors and important messages
        if '200' not in str(args):
            return
        return super().log_message(format, *args)


def serve(port=8000):
    """Start the HTTP server"""
    # Ensure static_site exists
    static_dir = Path('static_site')
    if not static_dir.exists():
        print("❌ static_site/ directory not found")
        print("   Run 'python generate_site.py' first")
        return

    server = HTTPServer(('localhost', port), AnalysisHandler)
    print(f"🏈 Super Bowl Analysis Server")
    print(f"   http://localhost:{port}")
    print(f"\n   Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        server.server_close()


if __name__ == "__main__":
    serve()
