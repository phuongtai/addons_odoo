import base64

from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.http import request
from openerp.osv import osv, fields


from openerp.addons.website.models.website import slug
class gamma_website(http.Controller):
    @http.route([
        '/homepage', 
    ], type='http', auth="public", website=True)
    def homepage(self):
        return request.website.render('gamma_website.homepage')