# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Test",
    'category': 'Generic Modules/Tools',
    'version': '19.0.1.0.0',
    'summary': 'Test Application',
    'description': """Test Application - Similar to Survey Module
This module provides test/assessment functionality with questions,
user inputs, and scoring capabilities.
    """,
    'author': 'Ashley',
    'website': '',
    'license': 'LGPL-3',
'depends': [
        'base',
        'mail',
    ],
'data': [
        'security/ir.model.access.csv',
        'views/test_survey_views.xml',
        'views/portal_templates.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
