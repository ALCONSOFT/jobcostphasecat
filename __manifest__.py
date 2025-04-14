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
                - Agregando Funcionalidad que oculta la linea de la SdP que no se compra. 2025.01.07:
                - Agregando funcionalidad que permite ver precios unitarios con descuentos en la SdP. 2025.01.08:
                - Agregando opcion de seleccionar vehiculo en la SdC-Solucion al tema de privilegio por flota. 2025.01.13:
                - Agregando funcionalidad de teminos de condiciones de pago: 2025.01.13:
                - Corrigiendo fallo al actualizar Cuanta Analitica y Analitico en la SdP. 2025.01.23:
                - Corrigiendo fallo al crear Picking en la SdP->O.C. 2025.01.24:
                - Corrigiendo funcionalidad de descuento general en la O.C.  solo se permite cambiar a desc gene es estados 
                    borrador, enviado y esperando por revisioin de precio. 2025.01.24: 
                - Agregando opcion de seleccionar vehiculo en la SdP-Solucion al tema de privilegio por flota. 2025.01.25:
                - Agregando funcionalidad de Fase en SdC, SdP, O.C., Factura. 2025.01.25:
                - Agregando funcionalidad de Boton de Regresar a Estado Anterior en O.C. 2025.01.27:
                -----------------------------------------------------------------------------------------
                - Agregando modificacion en reporte de O.C. personalizacion de Encabezado. 2025.01.30:
                    * Se debe deactivar el reporte qweb del modulo purchase_stcok.report_purchaseorder_document
                - Agregando restrincción de eliminacion de documentos en SdC, SdP, O.C. 2025.01.31:
                - Agregando funcionalidad para fusionar archivos adjuntos al correo. 2025.02.01:
                    - Corrigiendo incidencia donde los correos no se marcaban como enviados. 2025.02.11:
                    - Corrigiendo incidencia de privielgios.  Se creo Privilegio de Usuario Interno para adjuntos. 2025.02.12:
                -----------------------------------------------------------------------------------------
                - Agregando funcionalidad: Agregar botón que permita crear una SdP en Transferencia Interna y
                    enlace la SdP con la transferencia interna del inventario. 2025.02.13:
                - Corrigiendo incidencia: El vehiculo no pasa de O.C. a la factura. 2025.02.14:
                - Corrigiendo incidencia: Cambio de termino: Vendedor por Usuario en vista: Lista de SdP. 2025.02.14:
                - Agregando funcionalidad: Permitir que la cantidad del producto pedido se pueda modificar en la SdP
                    en los estados: draft, sent y waiting_for_price_revision. 2025.02.18
                - Corrigiendo incidencia: Solo Compras puede realizar cambios en la cantidad en la SdP. 2025.02.19
                - Corrigiendo incidencia: Implementar secciones y notas a la SdC: 2025.02.18
                - Corrigiendo incidencia: cambiando la logica de las entregas de Proveedores INternos
                    - cambaindo la ubicaion origen
                    - creando dos transferencias: 1 salida del almacen origen y 1 entrada al almacen destino: 2025.02.24
                - Corrigiendo incidencia: Agregando funcionalidades: Agregar al “lineas de pedidos de compra”:
                     - la cuenta analitica,
                     - analitico,
                     - fase,
                     - vehiculo.
                     - Enlace a la SdP. 
                -----------------------------------------------------------------------------------------                
                - Agregar funcionanalidad: Habilitar bitácora del modelo: product_template
                - Elimnar funcionalidad: memorizar los vehhiculos en la SdC. 2025.02.25
                - NO DISPONIBLE: Agregando funcionalidad: Agregar montos exentos de impuestos y no exentos en al Orden de Compra. 2025.02.25
                - Inhabilitar opcion de: action_views_details en stock.move. 2025.02.26
                - Agregando funcionalidad: recalcular estatus de la factura en las SdP. 2025.02.26
                - Agregando funcionalidad: Agregar filtro de cantidades recibidas != de cantidades pedidas en la SdP. 2025.02.26
                - Agregando funcionalidas:
                    Historial de cantidades pedidas, precios de Productos a nivel de SdC, Órdenes de Compras.
                    Para ser agregados en una pestaña nueva del Form de la orden de compra. 2025.02.26
                - Corrigiendo incidencia: No dejar crear mas SdP si ya se han creado. 2025.02.26
                -----------------------------------------------------------------------------------------
                - Corrigiendo incidencia: el campo descriocion no deja avanzar al momento de especificar los proveedores en PR. 2025.03.26
                - Corrigiendo incidencia: Agregar a la O.C. la cuenta Analitica - Analitico. 2025.03.27
                -----------------------------------------------------------------------------------------
                - Agregando funcionalidad: Agregar un campo user para filtar los almacenes por usuario. 2025.04.05
                - Agregando funcionalidad: Agregar un plantilla con enlace de la SdP o SdP. 2025.04.07
                - Agregando funcionalidad: Agregar un direcciones de correos de los destinarios en el correo. 2025.04.08
                -------------------------------------------------------------------------------------------
                - Corrigiendo incidencia: cuenta anlitica de linea de SdC por default copiarla del encabezado. 2025.04.14
                
    """,

    'author': "Alconsoft",
    'website': "http://www.alconsoft.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Job Cost',
    'version': '2025.04.14 - 12:20',

    # any module necessary for this one to work correctly
    'depends': ['bi_odoo_project_phases',
                'stock_analytic',
                'ethics_purchase_request',
                'purchase',
                'purchase_discount',
                'purchase_order_supplierinfo_update',    # Modulo que actualiza la información del precio del proveedor en la orden de compra
                'purchase_order_general_discount',       # Modulo que agrega descuento general a la orden de compra
                'account_fleet',                         # Modulo que agrega vehiculos a la factura
                'email_template_qweb',                   # Modulo que permite ediar vistas de qweb para correos en templates
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
        'report/purchase_order_report.xml',
        'views/view_account_move.xml',
        'views/views_res_partners.xml',
        'views/views_purchase_order_line_tree.xml',
        'report/reports_purchase.xml',
        'security/purchase_request_rules.xml',
        'data/email_templates_jc.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',

    ],
    # Aplicacion:  si aparace cierto (true) esta modulo sera una aplicacion que aprecera en el listado de aplicaciones de odoo.
    'application': True,
}
