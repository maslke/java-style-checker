import io
import os
import sys
import datetime

from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
import urllib.parse
import html


class RequestHandler(SimpleHTTPRequestHandler):
    """
    自定义Request Handler，展示文件列表的时候，展示文件创建的时间
    """
    def __init__(self, *args, directory=None, **kwargs):
        """

        :param args: args
        :param directory: 托管的目录
        :param kwargs: kwargs
        """
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        """
        处理 get 请求
        :return:
        """
        super().do_GET()

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            files = os.listdir(path)
        except OSError:
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "No permission to list directory")
            return None
        files.sort(key=lambda a: a.lower())
        r = []
        enc = sys.getfilesystemencoding()
        title = 'Check Result Files:'
        r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
                 '"http://www.w3.org/TR/html4/strict.dtd">')
        r.append('<html>\n<head>')
        r.append('<meta http-equiv="Content-Type" '
                 'content="text/html; charset=%s">' % enc)
        r.append('<title>%s</title>\n</head>' % title)
        r.append('<body>\n<h1>%s</h1>' % title)
        r.append('<hr>\n<ul>')
        if len(files) == 0:
            r.append('😖,it seems that you got an empty result.')
        else:
            for name in files:
                fullname = os.path.join(path, name)
                display_name = link_name = name
                # Append / for directories or @ for symbolic links
                if os.path.isdir(fullname):
                    display_name = name + "/"
                    link_name = name + "/"
                if os.path.islink(fullname):
                    display_name = name + "@"
                    # Note: a link to a directory displays with @ and links with /
                quoted_name = urllib.parse.quote(link_name, errors='surrogatepass')
                escaped_name = html.escape(display_name, quote=False)
                modify_time = os.path.getmtime(fullname)
                # 将时间戳转换为可读的日期时间格式
                creation_time = datetime.datetime.fromtimestamp(modify_time)
                r.append(f'<li><a href="{quoted_name}">{escaped_name}</a>, Created At {creation_time}</li>')
        r.append('</ul>\n<hr>\n</body>\n</html>\n')
        encoded = '\n'.join(r).encode(enc, 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f
