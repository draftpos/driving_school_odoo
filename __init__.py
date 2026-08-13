# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import models
from . import controllers

def _hide_apps(env):
    """
    Hide specific apps' root menus if they are installed.
    This runs when the test app is installed.
    """
    menu_xml_ids = [
        'sale.sale_menu_root',                                 # Sales
        'account.menu_finance',                                # Accounting
        'account_accountant.menu_accounting',                  # Accounting (Enterprise)
        'purchase.menu_purchase_root',                         # Purchase
        'hr_expense.menu_hr_expense_root',                     # Expenses
        'contacts.menu_contacts',                              # Contacts
        'website.menu_website_configuration',                  # Websites
        'spreadsheet_dashboard.spreadsheet_dashboard_menu_root', # Dashboards
    ]
    
    for xml_id in menu_xml_ids:
        menu = env.ref(xml_id, raise_if_not_found=False)
        if menu:
            menu.active = False
