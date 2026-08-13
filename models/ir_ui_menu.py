# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, tools

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('frozenset(self.env.user._get_group_ids())', 'debug')
    def _visible_menu_ids(self, debug=False):
        menus = super()._visible_menu_ids(debug=debug)
        
        hidden_xml_ids = [
            'sale.sale_menu_root',
            'account.menu_finance',
            'account_accountant.menu_accounting',
            'purchase.menu_purchase_root',
            'hr_expense.menu_hr_expense_root',
            'contacts.menu_contacts',
            'website.menu_website_configuration',
            'spreadsheet_dashboard.spreadsheet_dashboard_menu_root',
        ]
        
        hidden_ids = set()
        for xml_id in hidden_xml_ids:
            menu = self.env.ref(xml_id, raise_if_not_found=False)
            if menu:
                hidden_ids.add(menu.id)
                
        return frozenset(menus - hidden_ids)
