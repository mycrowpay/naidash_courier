# -*- coding: utf-8 -*-
{
    'name': "NaiDash Courier Services",

    'summary': "NaiDash Courier Management System",

    'description': """
        NaiDash is a Courier Management System
    """,

    'author': "NaiDash",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/17.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Naidash',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'courier_manage', 'naidash_sms'],

    # always loaded
    'data': [
        # 'security/groups.xml',
        'security/ir.model.access.csv',
        # 'data/ir_sequence_data.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/courier.xml',
        'views/settings.xml',
        'data/sms_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,    
    'license': 'LGPL-3',        
}

