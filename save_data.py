from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from urllib.parse import parse_qs
import logging
import traceback

# إعداد التسجيل
logging.basicConfig(
    filename='save_errors.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SaveDataHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            # تسجيل معلومات الطلب
            logging.info(f"Received POST request from {self.client_address[0]}")
            logging.info(f"Headers: {dict(self.headers)}")

            # قراءة طول البيانات
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError('لم يتم استلام أي بيانات')

            post_data = self.rfile.read(content_length)
            logging.debug(f"Received raw data: {post_data.decode('utf-8')}")
            
            # تحليل البيانات
            if self.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                data = parse_qs(post_data.decode('utf-8'))
                logging.debug(f"Parsed form data: {data}")
                
                if 'data' not in data:
                    raise ValueError('لم يتم العثور على البيانات في الطلب')
                
                try:
                    json_data = json.loads(data['data'][0])
                except json.JSONDecodeError as e:
                    logging.error(f"JSON decode error in form data: {str(e)}")
                    raise ValueError(f'خطأ في تنسيق البيانات: {str(e)}')
            else:
                try:
                    json_data = json.loads(post_data.decode('utf-8'))
                except json.JSONDecodeError as e:
                    logging.error(f"JSON decode error in raw data: {str(e)}")
                    raise ValueError(f'خطأ في تنسيق البيانات: {str(e)}')

            # التحقق من هيكل البيانات
            if not isinstance(json_data, dict):
                raise ValueError('البيانات المرسلة يجب أن تكون كائن JSON')
            
            logging.debug(f"Received JSON data: {json.dumps(json_data, ensure_ascii=False)}")

            # التحقق من وجود الملف
            file_path = 'data.json'
            if not os.path.exists(file_path):
                logging.info("Creating new data.json file")
                initial_data = {
                    'movies': [],
                    'series': [],
                    'featured': []
                }
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(initial_data, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    logging.error(f"Error creating file: {str(e)}")
                    raise ValueError('لا يمكن إنشاء الملف data.json')

            # التحقق من صلاحيات الكتابة
            if not os.access(file_path, os.W_OK):
                logging.error(f"File is not writable: {file_path}")
                raise ValueError('لا يمكن الكتابة في الملف data.json')

            # حفظ البيانات في الملف
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                logging.info("Data saved successfully")
            except Exception as e:
                logging.error(f"Error writing to file: {str(e)}")
                raise ValueError('فشل في حفظ البيانات في الملف')

            # إرسال رد نجاح
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = json.dumps({
                'success': True,
                'message': 'تم حفظ البيانات بنجاح'
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))

        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {str(e)}")
            self.send_error_response('البيانات المرسلة غير صالحة: ' + str(e))
        except ValueError as e:
            logging.error(f"Validation error: {str(e)}")
            self.send_error_response(str(e))
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            self.send_error_response('حدث خطأ غير متوقع: ' + str(e))

    def send_error_response(self, message):
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = json.dumps({
            'success': False,
            'message': message
        }, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SaveDataHandler)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server() 