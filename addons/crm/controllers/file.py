import os
from odoo import http
from odoo.http import request
from odoo.tools import config
from werkzeug.wrappers import Response


class FileDownloadController(http.Controller):
    @http.route('/uploads/<path:file_path>', type='http', auth='user')
    def download_file(self, file_path, **kwargs):
        root_path = config['root_path'][:-4]
        file_full_path = os.path.join(root_path, 'uploads', file_path)
        print(file_full_path)

        if os.path.exists(file_full_path):
            with open(file_full_path, 'rb') as file:
                file_data = file.read()

            headers = [('Content-Type', 'application/octet-stream'),
                       ('Content-Disposition', f'attachment; filename={os.path.basename(file_full_path)}')]

            return request.make_response(file_data, headers=headers)
        else:
            return Response('File not found', status=404)
