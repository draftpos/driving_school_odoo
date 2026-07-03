# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Driving School Test",
    'category': 'Generic Modules/Tools',
    'version': '19.0.1.0.4',
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
        'website',
        'portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/test_survey_views.xml',
        'views/test_settings_views.xml',
        'views/portal_templates.xml',
        'data/default_student_data.xml',
        'data/update_data.xml',
],
    'assets': {
        'web.assets_frontend': [
            'test/static/src/css/test_portal.css',
            'test/static/src/css/custom_register.css',
            'test/static/src/js/test_portal.js',
        ],
        'web.assets_backend': [
            'test/static/src/css/backend.css',
        ],
    },
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
