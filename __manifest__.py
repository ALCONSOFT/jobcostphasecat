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
                - Agregando funcion que agrega parametros de almacen y vehiculo al pase al SdP
                - Agregando picking_type_id
                - Agregando valores_Defaults por modelo
                - Agregando estado: Esperando por Auditoria
                - Agregando vehicle al modelo back.purhcase.request
                - Agregando Flujo de Estado en Solicitud de Presupuesto & O.C.
                    - waiting_for_price_revision
                    - waiting_for_price_approval
                    - waiting_for_approval
                    - waiting_for_audit
                    - waiting_for_buyer
                - Agregando colores a los estados agregados
                - Agregando vista kanban al modelo purchase.request
                - Arreglando vista Form heredada que no funcionaba - purchase.request.form.inherit.ethicspr
                - Creando cuenta analitica predetetermianda por almacen. 2024.12.20
                - Agregando vehiculo a la vista de formulario de salidas de almacen. 2024.12.23: 
                - Agregando funcionalidad que impide crear partners en la vista SdC. 2024.12.27:
                - Corrigiendo consulta sql que filtra las secuencias de mas de 2 digitos en SdC. 2024.12.31:
                - Agregando Reporte de SdC. 2024.12.31:
    """,

    'author': "Alconsoft",
    'website': "http://www.alconsoft.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Job Cost',
    'version': '25.01.01:18',

    # any module necessary for this one to work correctly
    'depends': ['bi_odoo_project_phases',
                'stock_analytic',
                'ethics_purchase_request',
                'purchase',
                ],

    # always loaded: Aqui se cargan los formularios de vista.
    # IMPORTANTE: SE QUITA EL CARACTER "#" PARA QUE SE PUEDA CARGAR ARCHIVO CON LA LISTA DE ACCESO DE SEGURIDAD
    'data': [
        ####### ESTO IMPEDIA QUE SE PUDIERA VER EL MENU ########################
        'security/security_view.xml',
        'security/ir.model.access.csv',
        ###############################
        'views/res_config_settings_views.xml',
        'views/views2.xml',
        'views/views_categories.xml',
        #'views/views_reports.xml',
        'views/view_picking.xml',
        ###############################
        'report/purchase_request_report_template.xml',
        'report/purchase_request_report_action.xml',
        ###############################
        'views/views_ethics_purchase_request.xml',
        'views/views_purchase_order.xml',
        'static/xls/project.costtype.csv',
        'static/xls/project.category.csv',
        #'views/view_purchase_approval_kanak.xml',
        'views/news_views.xml',
        'views/res_company_view.xml',
        'views/views_stock_warehouse.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',

    ],
    # Aplicacion:  si aparace cierto (true) esta modulo sera una aplicacion que aprecera en el listado de aplicaciones de odoo.
    'application': True,
}
