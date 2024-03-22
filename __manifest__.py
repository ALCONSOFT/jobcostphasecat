# -*- coding: utf-8 -*-
{
    'name': "jobcostphasecat",

    'summary': """
        Gestión de Proyectos por Fase y Categoría""",

    'description': """
        - Modelo y Vista: Categorías
        - Herencia de Fases y Categorías en Operaciones Inventario
            - stock.picking, stock.move, stock.move.line
            - Basarse en modulo: stock_analytic: cuenta analítica modulo de Inventario.
            - Agregando por codigo validación de fecha de cierre [close_date]
            - Agregando cambios para compatibilidad con odoo 16:
                - iteracción con account Analytic Distribution en Transferencias
                - Agregando a linea de las compras el vehículo y Cuenta Analítica
                  al que se le realiza la compra
                - *****
    """,

    'author': "Alconsoft",
    'website': "http://www.alconsoft.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Job Cost',
    'version': ' -> 24.03.22-17:00',

    # any module necessary for this one to work correctly
    'depends': ['bi_odoo_project_phases',
                'stock_analytic',
                'ethics_purchase_request'],

    # always loaded: Aqui se cargan los formularios de vista.
    # IMPORTANTE: SE QUITA EL CARACTER "#" PARA QUE SE PUEDA CARGAR ARCHIVO CON LA LISTA DE ACCESO DE SEGURIDAD
    'data': [
        ####### ESTO IMPEDIA QUE SE PUDIERA VER EL MENU ########################
        'security/ir.model.access.csv',
        ###############################
        'views/views2.xml',
        'views/views_categories.xml',
        #'views/views_reports.xml',
        'views/view_picking.xml',
        'views/views_ethics_purchase_request.xml',
        'static/xls/project.costtype.csv',
        'static/xls/project.category.csv',
        ###############################
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',

    ],
    # Aplicacion:  si aparace cierto (true) esta modulo sera una aplicacion que aprecera en el listado de aplicaciones de odoo.
    'application': True,
}