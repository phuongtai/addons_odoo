import openerp
from openerp import SUPERUSER_ID
from openerp import http
from openerp import tools
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website_sale.controllers.main import website_sale
from openerp.addons.website_sale.controllers.main import QueryURL

#THANH: Get pricelist from website set
def get_pricelist():
    return request.website.get_current_pricelist()

class ecom_demo(openerp.addons.web.controllers.main.Home):
    
    #THANH: Get pricelist
    def get_pricelist(self):
        return get_pricelist()
    
    @http.route('/page/<page:page>', type='http', auth="public", website=True, cache=300)
    def page(self, page, **opt):
        values = {
            'path': page,
            'deletable': True, # used to add 'delete this page' in content menu
        }
        
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)
            
        order = request.website.sale_get_order()
        if order:
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
        else:
            compute_currency = lambda price: price
        
        values.update({
            'website_sale_order': order,
            'compute_currency': compute_currency,
            'pricelist': pricelist,
        })
        
        if not hasattr(request.website, 'keep'):
            keep = QueryURL('/shop', category=0, search='', attrib=[])
            values.update({
                'keep': keep,
            })
        
        if not hasattr(request.website, 'new_products'):
            domain = [('sale_ok', '=', True)]
            product_obj = pool.get('product.template')
            product_ids = product_obj.search(cr, uid, domain, limit=10, offset=None, order='website_published desc, website_sequence desc', context=context)
            new_products = product_obj.browse(cr, uid, product_ids, context=context)
            
            
            values.update({
                'new_products': new_products,
            })
        
        #THANH: Categ Laptop
        if not hasattr(request.website, 'new_categ_laptops'):
            domain = [('sale_ok', '=', True),('public_categ_ids.name', '=', 'Laptops')]
            product_obj = pool.get('product.template')
            product_ids = product_obj.search(cr, uid, domain, limit=10, offset=None, order='website_published desc, website_sequence desc', context=context)
            new_categ_laptops = product_obj.browse(cr, uid, product_ids, context=context)
            values.update({
                'new_categ_laptops': new_categ_laptops,
            })
        
        #THANH: Categ Network
        if not hasattr(request.website, 'new_categ_networks'):
            domain = [('sale_ok', '=', True),('public_categ_ids.name', '=', 'Network')]
            product_obj = pool.get('product.template')
            product_ids = product_obj.search(cr, uid, domain, limit=10, offset=None, order='website_published desc, website_sequence desc', context=context)
            new_categ_networks = product_obj.browse(cr, uid, product_ids, context=context)
            values.update({
                'new_categ_networks': new_categ_networks,
            })
            
        # /page/website.XXX --> /page/XXX
        if page.startswith('website.'):
            return request.redirect('/page/' + page[8:], code=301)
        elif '.' not in page:
            page = 'website.%s' % page

        try:
            request.website.get_template(page)
        except ValueError, e:
            # page not found
            if request.website.is_publisher():
                values.pop('deletable')
                page = 'website.page_404'
            else:
                return request.registry['ir.http']._handle_exception(e, 404)

        return request.render(page, values)

class custom_website_sale(website_sale):
    #tai custom
    @http.route(['/'], type='http', auth="public", website=True)
    def homepage(self):
        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)
        values ={
                 'categories':categs
        }
        return request.website.render("ecom_demo.custom_layout",values)
        
     
    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def checkout(self, **post):
        cr, uid, context = request.cr, request.uid, request.context
 
        order = request.website.sale_get_order(force_create=1, context=context)
 
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection
 
        values = self.checkout_values()
         
        #THANH:
        pool = request.registry
        if order:
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
        else:
            compute_currency = lambda price: price
 
        values.update({
            'website_sale_order': order,
            'compute_currency': compute_currency,
        })
        #THANH:
         
        return request.website.render("website_sale.checkout", values)
     
    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    def confirm_order(self, **post):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
 
        order = request.website.sale_get_order(context=context)
        if not order:
            return request.redirect("/shop")
 
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection
 
        values = self.checkout_values(post)
         
        #THANH:
        pool = request.registry
        if order:
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
        else:
            compute_currency = lambda price: price
        values.update({
            'website_sale_order': order,
            'compute_currency': compute_currency,
        })
        #THANH:
         
        values["error"], values["error_message"] = self.checkout_form_validate(values["checkout"])
        if values["error"]:
            return request.website.render("website_sale.checkout", values)
 
        self.checkout_form_save(values["checkout"])
 
        request.session['sale_last_order_id'] = order.id
 
        request.website.sale_get_order(update_pricelist=True, context=context)
 
        extra_step = registry['ir.model.data'].xmlid_to_object(cr, uid, 'website_sale.extra_info_option', raise_if_not_found=True)
        if extra_step.active:
            return request.redirect("/shop/extra_info")
 
        return request.redirect("/shop/payment")
      
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        """ Payment step. This page proposes several payment means based on available
        payment.acquirer. State at this point :
 
         - a draft sale order with lines; otherwise, clean context / session and
           back to the shop
         - no transaction in context / session, or only a draft one, if the customer
           did go to a payment.acquirer website but closed the tab without
           paying / canceling
        """
        cr, uid, context = request.cr, request.uid, request.context
        payment_obj = request.registry.get('payment.acquirer')
        sale_order_obj = request.registry.get('sale.order')
 
        order = request.website.sale_get_order(context=context)
 
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection
 
        shipping_partner_id = False
        if order:
            if order.partner_shipping_id.id:
                shipping_partner_id = order.partner_shipping_id.id
            else:
                shipping_partner_id = order.partner_invoice_id.id
 
        values = {
            'website_sale_order': order
        }
        values['errors'] = sale_order_obj._get_errors(cr, uid, order, context=context)
        values.update(sale_order_obj._get_website_data(cr, uid, order, context))
 
        if not values['errors']:
            # find an already existing transaction
            tx = request.website.sale_get_transaction()
            acquirer_ids = payment_obj.search(cr, SUPERUSER_ID, [('website_published', '=', True), ('company_id', '=', order.company_id.id)], context=context)
            values['acquirers'] = list(payment_obj.browse(cr, uid, acquirer_ids, context=context))
            render_ctx = dict(context, submit_class='btn btn-primary', submit_txt=_('Pay Now'))
            for acquirer in values['acquirers']:
                acquirer.button = payment_obj.render(
                    cr, SUPERUSER_ID, acquirer.id,
                    tx and tx.reference or request.env['payment.transaction'].get_next_reference(order.name),
                    order.amount_total,
                    order.pricelist_id.currency_id.id,
                    values={
                        'return_url': '/shop/payment/validate',
                        'partner_id': shipping_partner_id
                    },
                    context=render_ctx)
         
        #THANH:
        pool = request.registry
        if order:
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
        else:
            compute_currency = lambda price: price
        values.update({
            'website_sale_order': order,
            'compute_currency': compute_currency,
        })
        #THANH:
         
        return request.website.render("website_sale.payment", values)
    