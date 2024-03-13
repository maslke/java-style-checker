import os
import socket
import webbrowser
from http.server import HTTPServer
import psutil

from handler.RequestHandler import RequestHandler


def run_server(server_class=HTTPServer, handler_class=RequestHandler, port=8000, base_dir='.'):
    server_address = ('', port)
    handler_class.base_dir = base_dir

    class MyRequestHandler(RequestHandler):

        def __init__(self, *args, **kwargs):
            self.directory = base_dir
            super().__init__(*args, directory=base_dir, **kwargs)

    httpd = server_class(server_address, MyRequestHandler)
    print(f'Starting server on port {port}, serving directory {handler_class.base_dir}...')
    httpd.serve_forever()


def port_is_valid(web_port):
    """
    检查端口是否被占用
    :param web_port: 端口地址
    :return:
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', web_port))
        except socket.error:
            return True
        return False


def kill_process_using_port(port):
    """
    杀掉占用端口的进程
    :param port: 端口号
    :return:
    """
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conns in proc.connections(kind='inet'):
                if conns.laddr.port == port:
                    proc.terminate()
                    print(f"Process with PID {proc.pid} killed successfully.")
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            pass


def kill_process_using_name(name):
    """
    根据进程名称杀死进程
    :param name:
    :return:
    """
    proc_list = []
    for proc in psutil.process_iter(['pid', 'name', 'ppid']):
        try:
            if name.lower() in proc.name().lower():
                proc_list.append(proc)
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            pass
    pid = os.getpid()
    current_process_list = []
    current_process_id_list = []
    current_process = list(filter(lambda x: x.pid == pid, proc_list))
    if len(current_process) > 0:
        current_process_list.extend(current_process)
        current_process_list.extend(list(filter(lambda x: x.pid == current_process[0].ppid(), proc_list)))
        current_process_id_list.extend([p.pid for p in current_process_list])
    for proc in proc_list:
        try:
            if proc.pid not in current_process_id_list:
                proc.terminate()
                print(f"Process with PID {proc.pid} killed successfully, By PID {pid}")
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            pass


def start_web_page(output_folder, web_port, auto_open):
    """
    开启web server
    :param output_folder: 目录
    :param web_port: web server 端口
    :param auto_open: 是否自动打开浏览器
    :return:
    """
    print(f'visit http://localhost:{web_port}')
    kill_process_using_port(web_port)
    if auto_open:
        webbrowser.open_new_tab(f'http://localhost:{web_port}')
    run_server(port=web_port, base_dir=output_folder)
    return 0
