"""
Vyaas AI Desktop Launcher
Uses Pywebview to display Next.js frontend in a native window
and manages the backend LiveKit agent as a subprocess.
"""

import webview
import subprocess
import threading
import time
import os
import sys
import signal
import atexit
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

# Configuration
WINDOW_TITLE = "Vyaas AI"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
MINI_WIDTH = 580  # Width for full control bar
MINI_HEIGHT = 80  # Height for control bar
STATIC_PORT = 3000  # Port for serving static files
BACKEND_READY_DELAY = 3  # Seconds to wait for backend to start

# Global reference for window communication
_main_window = None
_mini_window = None
_is_mini_mode = False
_room_data = None  # Stores {serverUrl, token} for mini mode


class MiniToolbarAPI:
    """API for mini toolbar window"""
    
    def expand_to_full(self):
        """Expand back to full window"""
        global _main_window, _mini_window, _is_mini_mode
        if _main_window and _mini_window:
            _mini_window.hide()
            _main_window.show()
            _is_mini_mode = False
            return {"success": True}
        return {"success": False}
    
    def get_room_data(self):
        """Get stored room data for mini mode connection"""
        global _room_data
        if _room_data:
            return {"success": True, "data": _room_data}
        return {"success": False, "data": None}

    def toggle_mic(self):
        """Toggle microphone in main window"""
        global _main_window
        if _main_window:
            _main_window.evaluate_js("if(window.vyaasParams && window.vyaasParams.toggleMic) window.vyaasParams.toggleMic()")
            return {"success": True}
        return {"success": False}

    def toggle_camera(self):
        """Toggle camera in main window"""
        global _main_window
        if _main_window:
            _main_window.evaluate_js("if(window.vyaasParams && window.vyaasParams.toggleCamera) window.vyaasParams.toggleCamera()")
            return {"success": True}
        return {"success": False}

    def toggle_screen(self):
        """Toggle screen share in main window"""
        global _main_window
        if _main_window:
            _main_window.evaluate_js("if(window.vyaasParams && window.vyaasParams.toggleScreen) window.vyaasParams.toggleScreen()")
            return {"success": True}
        return {"success": False}


class WindowAPI:
    """JavaScript API exposed to frontend for window controls"""
    
    def __init__(self):
        self._is_fullscreen = False
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode (F12)"""
        global _main_window
        if _main_window:
            self._is_fullscreen = not self._is_fullscreen
            _main_window.toggle_fullscreen()
            return {"success": True, "fullscreen": self._is_fullscreen}
        return {"success": False}
    
    def toggle_mini_mode(self):
        """Toggle between mini floating mode and normal mode"""
        global _main_window, _mini_window, _is_mini_mode
        
        if _is_mini_mode:
            # Expand to full
            if _mini_window:
                _mini_window.hide()
            if _main_window:
                _main_window.show()
            _is_mini_mode = False
            return {"success": True, "mini": False}
        else:
            # Enter mini mode (Overlay)
            # Do NOT hide main window - user wants overlay behavior
            # if _main_window:
            #     _main_window.hide()
            if _mini_window:
                _mini_window.show()
                # Ensure it's on top
                
            _is_mini_mode = True
            return {"success": True, "mini": True}
    
    def get_window_state(self):
        """Get current window state"""
        global _is_mini_mode
        return {
            "is_mini_mode": _is_mini_mode,
            "is_fullscreen": self._is_fullscreen
        }
    
    def set_room_data(self, server_url: str, token: str):
        """Store room data for mini mode"""
        global _room_data
        _room_data = {"serverUrl": server_url, "token": token}
        print(f"Room data stored for mini mode")
        return {"success": True}
    
    def clear_room_data(self):
        """Clear room data when session ends"""
        global _room_data
        _room_data = None
        return {"success": True}
    
    def get_room_data(self):
        """Get room data (for main window to check)"""
        global _room_data
        if _room_data:
            return {"success": True, "data": _room_data}
        return {"success": False, "data": None}

class VyaasDesktopApp:
    def __init__(self):
        self.backend_process = None
        self.http_server = None
        self.http_thread = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Frontend static files location (Next.js 'out' folder)
        self.frontend_dir = os.path.join(self.base_dir, '..', 'Frontend', 'out')
        
        # For PyInstaller bundled app
        if getattr(sys, 'frozen', False):
            # When bundled, base_dir is where the EXE is
            self.base_dir = os.path.dirname(sys.executable)
            # Frontend is in _internal/frontend (PyInstaller puts data there)
            internal_dir = os.path.join(self.base_dir, '_internal')
            self.frontend_dir = os.path.join(internal_dir, 'frontend')
            
            # Fallback: try next to EXE
            if not os.path.exists(self.frontend_dir):
                self.frontend_dir = os.path.join(self.base_dir, 'frontend')
        
        print(f"Base Directory: {self.base_dir}")
        print(f"Frontend Directory: {self.frontend_dir}")
        
        # Storage path for persistent sessions (login data, localStorage, etc.)
        self.storage_path = os.path.join(self.base_dir, 'vyaas_data')
        os.makedirs(self.storage_path, exist_ok=True)
        print(f"Storage Path: {self.storage_path}")
    
    def _set_zoom(self, window):
        """Reset zoom level to 100% after window loads"""
        import time
        time.sleep(1)  # Wait for page to load
        
        # Reset zoom to 65% for proper scaling on high DPI displays
        try:
            window.evaluate_js("""
                document.body.style.zoom = '65%';
                document.body.style.transform = 'scale(1)';
                document.body.style.transformOrigin = 'top left';
            """)
            print("Zoom level adjusted to 65%")
        except Exception as e:
            print(f"Could not set zoom: {e}")
        
    def start_static_server(self):
        """Start HTTP server to serve Next.js static files"""
        if not os.path.exists(self.frontend_dir):
            print(f"ERROR: Frontend directory not found: {self.frontend_dir}")
            return False
            
        os.chdir(self.frontend_dir)
        
        handler = partial(SilentHTTPHandler, directory=self.frontend_dir)
        self.http_server = HTTPServer(('127.0.0.1', STATIC_PORT), handler)
        
        self.http_thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
        self.http_thread.start()
        
        print(f"Static server running at http://127.0.0.1:{STATIC_PORT}")
        return True
        
    def start_backend(self):
        """Start the LiveKit backend agent"""
        backend_script = os.path.join(self.base_dir, 'agent.py')
        
        # For PyInstaller bundled app, look for compiled backend
        if getattr(sys, 'frozen', False):
            # Check mode from env (loaded by First Run Wizard just now)
            mode = os.getenv("VYAAS_MODE", "local").lower()
            
            if mode == "cloud":
                bridge_exe = os.path.join(self.base_dir, 'vyaas_desktop_bridge.exe')
                print(f"Starting bundled bridge: {bridge_exe}")
                if os.path.exists(bridge_exe):
                    self.backend_process = subprocess.Popen(
                        [bridge_exe],
                        cwd=self.base_dir,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                    return True
            else:
                backend_exe = os.path.join(self.base_dir, 'VyaasAI_Brain.exe')
                if os.path.exists(backend_exe):
                    print(f"Starting bundled backend: {backend_exe}")
                    self.backend_process = subprocess.Popen(
                        [backend_exe, 'dev'],
                        cwd=self.base_dir,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                    return True
        
        # Development mode - run Python script
        if os.path.exists(backend_script):
            python_exe = sys.executable
            venv_python = os.path.join(self.base_dir, 'venv', 'Scripts', 'python.exe')
            
            if os.path.exists(venv_python):
                python_exe = venv_python
            
            # Check for Cloud Mode (Lightweight Client)
            mode = os.getenv("VYAAS_MODE", "local").lower()
            if mode == "cloud":
                print("[INFO] VYAAS running in CLOUD MODE")
                script_to_run = os.path.join(self.base_dir, 'vyaas_desktop_bridge.py')
                print(f"Starting Desktop Bridge: {script_to_run}")
            else:
                print("[INFO] VYAAS running in LOCAL MODE")
                script_to_run = backend_script
                print(f"Starting Backend Agent: {script_to_run}")

            if not os.path.exists(script_to_run):
                 print(f"ERROR: Script not found: {script_to_run}")
                 return False

            self.backend_process = subprocess.Popen(
                [python_exe, script_to_run, 'dev'],
                cwd=self.base_dir,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            return True
        else:
            print(f"WARNING: Backend script not found: {backend_script}")
            return False
            
    def stop_backend(self):
        """Stop the backend process"""
        if self.backend_process:
            print("Stopping backend...")
            if sys.platform == 'win32':
                self.backend_process.terminate()
            else:
                self.backend_process.send_signal(signal.SIGTERM)
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            self.backend_process = None
            
    def stop_server(self):
        """Stop the HTTP server"""
        if self.http_server:
            print("Stopping static server...")
            self.http_server.shutdown()
            self.http_server = None
            
    def cleanup(self):
        """Clean up all resources"""
        self.stop_backend()
        self.stop_server()
        print("Cleanup complete.")
        
    def run(self):
        """Main entry point"""
        print("=" * 50)
        print("  VYAAS AI - Desktop Application")
        print("=" * 50)
        
        # Register cleanup
        atexit.register(self.cleanup)
        
        # Start static file server
        if not self.start_static_server():
            print("Failed to start static server. Exiting.")
            return
            
        # Start backend
        backend_started = self.start_backend()
        if backend_started:
            print(f"Waiting {BACKEND_READY_DELAY}s for backend to initialize...")
            time.sleep(BACKEND_READY_DELAY)
        
        # Create Window APIs
        main_api = WindowAPI()
        mini_api = MiniToolbarAPI()
        
        # Create main window
        print("Opening Vyaas AI window...")
        global _main_window, _mini_window
        
        _main_window = webview.create_window(
            WINDOW_TITLE,
            f'http://127.0.0.1:{STATIC_PORT}',
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            resizable=True,
            min_size=(800, 600),
            zoomable=True,
            js_api=main_api
        )
        
        # Create mini toolbar window (hidden by default) - loads /mini route
        _mini_window = webview.create_window(
            'VYAAS Mini',
            f'http://127.0.0.1:{STATIC_PORT}/mini',  # Load mini route from frontend
            width=MINI_WIDTH,
            height=MINI_HEIGHT,
            resizable=False,
            frameless=True,  # No title bar
            on_top=True,  # Always on top
            hidden=True,  # Start hidden
            js_api=mini_api
        )
        print("Mini toolbar window created (hidden) - using /mini route")
        
        # Setup function that runs after window loads
        def on_loaded(main_win):
            self._set_zoom(main_win)
            # Inject F12 and F11 keyboard listeners
            main_win.evaluate_js("""
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'F12') {
                        e.preventDefault();
                        if (window.pywebview && window.pywebview.api) {
                            window.pywebview.api.toggle_fullscreen();
                        }
                    }
                    // F11 for mini mode
                    if (e.key === 'F11') {
                        e.preventDefault();
                        if (window.pywebview && window.pywebview.api) {
                            window.pywebview.api.toggle_mini_mode();
                        }
                    }
                });
                console.log('Desktop keyboard shortcuts enabled: F12=Fullscreen, F11=Mini Mode');
            """)
        
        # Start webview with zoom fix and persistent storage
        webview.start(
            func=on_loaded,
            args=[_main_window],
            gui='edgechromium',
            storage_path=self.storage_path,
            private_mode=False
        )
        
        # Cleanup after window closes
        self.cleanup()


class SilentHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP handler that suppresses logs and handles SPA routing"""
    
    def log_message(self, format, *args):
        pass  # Suppress logs
        
    def do_GET(self):
        """Handle GET requests with SPA fallback for clean URLs"""
        # Check if file exists
        path = self.translate_path(self.path)
        
        if os.path.exists(path) and not os.path.isdir(path):
            # File exists, serve it
            return super().do_GET()
        elif os.path.exists(path + '.html'):
            # Try adding .html extension (Next.js static export)
            self.path = self.path + '.html'
            return super().do_GET()
        else:
            # Fallback to index.html for SPA routing
            self.path = '/index.html'
            return super().do_GET()


class SetupAPI:
    """API for the Setup Wizard"""
    def __init__(self, window):
        self.window = window
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
             self.base_dir = os.path.dirname(sys.executable)

    def save_config(self, data):
        """Save configuration to .env file"""
        env_path = os.path.join(self.base_dir, '.env')
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(f"LIVEKIT_URL={data.get('livekitUrl', '')}\n")
                f.write(f"LIVEKIT_API_KEY={data.get('livekitKey', '')}\n")
                f.write(f"LIVEKIT_API_SECRET={data.get('livekitSecret', '')}\n")
                f.write(f"GEMINI_API_KEY={data.get('geminiKey', '')}\n")
                f.write(f"VYAAS_MODE={data.get('mode', 'cloud')}\n")
                f.write(f"VYAAS_ROOM_NAME={data.get('roomName', 'vyaas_assist_room')}\n")
            
            print("[OK] Configuration saved!")
            self.window.destroy()
            return {"success": True}
        except Exception as e:
            print(f"[ERR] Failed to save config: {e}")
            return {"success": False, "error": str(e)}

    def close(self):
        self.window.destroy()


def run_setup_wizard():
    """Run the first-time setup wizard"""
    
    # HTML Content for Setup Wizard
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>VYAAS AI Setup</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #09090b; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .container { background: #18181b; padding: 2rem; border-radius: 12px; width: 400px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); border: 1px solid #27272a; }
            h2 { text-align: center; color: #8b5cf6; margin-top: 0; }
            .form-group { margin-bottom: 1rem; }
            label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; color: #a1a1aa; }
            input, select { width: 100%; padding: 0.75rem; background: #27272a; border: 1px solid #3f3f46; color: #fff; border-radius: 6px; box-sizing: border-box; outline: none; }
            input:focus { border-color: #8b5cf6; }
            button { width: 100%; padding: 0.75rem; background: #7c3aed; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 1rem; transition: background 0.2s; }
            button:hover { background: #6d28d9; }
            .note { font-size: 0.8rem; color: #71717a; margin-top: 1rem; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>VYAAS AI Setup</h2>
            <div class="form-group">
                <label>Mode</label>
                <select id="mode">
                    <option value="cloud">Cloud Client (Connect to Remote Brain)</option>
                    <option value="local">Local Brain (Run Locally)</option>
                </select>
            </div>
            <div class="form-group">
                <label>LiveKit URL</label>
                <input type="text" id="lk_url" placeholder="wss://..." value="wss://vyass-sxwzn7ti.livekit.cloud">
            </div>
            <div class="form-group">
                <label>LiveKit API Key</label>
                <input type="text" id="lk_key" placeholder="API Key">
            </div>
            <div class="form-group">
                <label>LiveKit API Secret</label>
                <input type="password" id="lk_secret" placeholder="API Secret">
            </div>
             <div class="form-group">
                <label>Gemini API Key (Optional for Cloud Mode)</label>
                <input type="password" id="gemini_key" placeholder="AI Studio Key">
            </div>
            <button onclick="save()">Save & Continue</button>
            <p class="note">These settings will be saved to .env</p>
        </div>
        <script>
            function save() {
                const data = {
                    mode: document.getElementById('mode').value,
                    livekitUrl: document.getElementById('lk_url').value,
                    livekitKey: document.getElementById('lk_key').value,
                    livekitSecret: document.getElementById('lk_secret').value,
                    geminiKey: document.getElementById('gemini_key').value,
                    roomName: 'vyaas_assist_room' 
                };
                
                if(!data.livekitKey || !data.livekitSecret) {
                    alert('LiveKit credentials are required!');
                    return;
                }
                
                window.pywebview.api.save_config(data);
            }
        </script>
    </body>
    </html>
    """
    
    window = webview.create_window('VYAAS AI Setup', html=html_content, width=500, height=700)
    window.expose(SetupAPI(window).save_config)
    webview.start()


def main():
    # Check for configuration
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        
    env_path = os.path.join(base_dir, '.env')
    
    # If no .env, run setup wizard
    if not os.path.exists(env_path):
        print("[WARN] Configuration not found. Running Setup Wizard...")
        run_setup_wizard()
        
        # Check again if created
        if not os.path.exists(env_path):
            print("[ERR] Setup cancelled. Exiting.")
            return

    from dotenv import load_dotenv
    load_dotenv(env_path)

    app = VyaasDesktopApp()
    app.run()


if __name__ == "__main__":
    main()
