#!/usr/bin/env python3
"""
سيرفر محلي لعرض قاعدة البيانات
يعمل على http://localhost:8000
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json
import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError

# إعدادات افتراضية
DEFAULT_API_URL = "https://clinic-ai-bot-backend-76pf.onrender.com"
DEFAULT_API_KEY = "E4QQpWs34YM_vMqKPcwvqiC1v7DSctaSyE0GNYJvf24"

class DatabaseViewerHandler(SimpleHTTPRequestHandler):
    """معالج مخصص لعرض قاعدة البيانات"""
    
    def do_GET(self):
        """معالجة طلبات GET"""
        if self.path == '/' or self.path == '/index.html':
            self.path = '/database-viewer.html'
        
        # إذا كان طلب API
        if self.path.startswith('/api/'):
            self.handle_api_request()
            return
        
        # عرض الملفات العادية
        return super().do_GET()
    
    def handle_api_request(self):
        """معالجة طلبات API"""
        try:
            # استخراج endpoint من المسار
            endpoint = self.path.replace('/api', '')
            
            # قراءة API key من query string أو استخدام الافتراضي
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            api_key = query_params.get('api_key', [DEFAULT_API_KEY])[0]
            api_url = query_params.get('api_url', [DEFAULT_API_URL])[0]
            
            # بناء URL كامل
            full_url = f"{api_url}{endpoint}"
            
            # إرسال طلب إلى Render API
            req = urllib.request.Request(full_url)
            req.add_header('X-API-Key', api_key)
            req.add_header('Content-Type', 'application/json')
            
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = response.read().decode('utf-8')
                    
                    # إرسال الرد
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(data.encode('utf-8'))
            except HTTPError as e:
                error_data = json.dumps({
                    'error': f'HTTP Error {e.code}: {e.reason}',
                    'message': e.read().decode('utf-8') if e.fp else ''
                })
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(error_data.encode('utf-8'))
            except URLError as e:
                error_data = json.dumps({
                    'error': f'Connection Error: {str(e)}'
                })
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(error_data.encode('utf-8'))
                
        except Exception as e:
            error_data = json.dumps({
                'error': f'Server Error: {str(e)}'
            })
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(error_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """تسجيل الرسائل"""
        print(f"[{self.address_string()}] {format % args}")


def run_server(port=8000):
    """تشغيل السيرفر"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DatabaseViewerHandler)
    
    print("=" * 60)
    print("🚀 سيرفر عرض قاعدة البيانات يعمل الآن!")
    print("=" * 60)
    print(f"📊 افتح المتصفح على: http://localhost:{port}")
    print(f"🔑 API Key الافتراضي: {DEFAULT_API_KEY}")
    print("=" * 60)
    print("اضغط Ctrl+C لإيقاف السيرفر")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹️  تم إيقاف السيرفر")
        httpd.server_close()


if __name__ == '__main__':
    import sys
    
    # تغيير المجلد إلى مجلد المشروع
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # قراءة المنفذ من السطر الأوامر
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("⚠️  منفذ غير صحيح، استخدام المنفذ الافتراضي 8000")
    
    run_server(port)

