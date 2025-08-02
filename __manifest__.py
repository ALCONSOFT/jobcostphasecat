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
                - Corrigiendo incidencia: Agregando funcionalidades: Agregar al "lineas de pedidos de compra":
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
                - Corrigiendo incidencia: Tradiciendo el formulario F-COM-01: 2025.04.28
                - Agregando funcionalidad: Agregar un campo de configuracion en compras para requerir
                    phase_id en SdC y Transferencias de Salidas. 2025.04.28,29
                - Moviendo funcionalidad: de ac_sync_odoo_odoo al modulo de jobcostphasecat plantilla y 
                    opcion configurable> Permitir duplicar solo transferencia en estado plantilla. 2025.05.02

                - Corrigiendo incidencia: cuenta anlitica de linea de SdC por default copiarla del encabezado. 2025.04.14
                ----------------------------------------------------------------------------------------------------------
                - Moviendo funcionalidad: de ac_sync_odoo_odoo al modulo de jobcostphasecat plantilla y 
                  opcion configurable> Permitir duplicar solo transferencia en estado plantilla. 2025.05.02
                - Agregando funcionalidad: campo numero de partes de fabricante en Product.template. 2025.06.03
                - Agregando funcionalidad: Gestión de descuentos en O.C. 2025.06.03
                - Agregando funcionalidad: Privielgios para Doble Transferencia Interna 2025.06.03
                -----------------------------------------------------------------------------------------
                - Agregando funcionalidad: Mover el boton [Descartar] al estado de O.C. [Revisión de Precio]. 2025.06.05
                - Agregando funcionalidad: Funcionalidad que permite cerrar manualmente el estado de facturación en una
                  orden de compra. De este modo, la orden de compra queda marcada como "cerrada". 2025.06.05
                -----------------------------------------------------------------------------------------
                - Agregando campos: Se agregan campos "Oculto en Reporte" y "Categoría Producto" a la vista árbol
                  de líneas de SdP ampliada (purchase.order.line.tree.jc). Ambos campos son opcionales pero 
                  se muestran inicialmente para facilitar el análisis de datos. 2025.08.01
                - Agregando campo: Se agrega campo "Referencia SdC" (pr_ref_ids) como primer campo en la vista,
                  permitiendo abrir el documento de Solicitud de Compra y ordenamiento. Campo modificado para
                  ser almacenado (store=True) y utiliza widget many2one_clickable. 2025.08.01
                - Agregando filtros y grupos: Se agregan filtros favoritos por Ref de SdC, Ref de Pedido, 
                  Proveedor, Producto, Order Date, Estado, Analítico, Distribución Analítica, Fase y Vehículo.
                  Grupos favoritos por Order Date, Proveedor, Categ. Prod. y Ref de SdC. 2025.08.01
                - Agregando colores a filas: Se implementan decoraciones de color en la vista árbol basadas
                  en estado (rojo=cancelado, gris=oculto, amarillo=esperando, azul=borrador/enviado, 
                  verde=compra, azul primario=hecho, negrita=incompleto). 2025.08.01
                - Corrigiendo error leyenda: Se remueve banner HTML incompatible con vistas árbol y se 
                  implementa leyenda de colores en el campo 'help' de la acción del menú. Se corrige
                  error tipográfico 'postion' por 'position'. 2025.08.01
                - Implementando leyenda efectiva: Se agrega leyenda de colores al nombre del menú con
                  iconos principales y filtro informativo completo en la vista de búsqueda con todas
                  las combinaciones de colores y sus significados. 2025.08.01
                - Agregando campos de tiempo de procesamiento: Se agregan campos Fecha SdC, Días Diferidos
                  y Horas Diferidas para analizar el tiempo entre solicitud y orden de compra. Incluye
                  filtros para procesamiento rápido/demorado y agrupación por días diferidos. 2025.08.01
                - Corrigiendo agrupación: Se modifica product_categ_id a store=True para permitir
                  agrupación por categoría de producto. Se corrige error XML con carácter especial. 2025.08.01
                - Implementando totales correctos: Se agregan campos price_subtotal_visible, price_total_visible
                  y price_tax_visible que excluyen automáticamente las líneas con Hide=True de los totales
                  de la vista árbol para cálculos precisos. 2025.08.01
                - Reordenando campos precio: Se reordenan campos en secuencia subtotal, total, subtotalvisible,
                  totalvisible y se hace configurable el campo subtotal original permitiendo ocultarlo/mostrarlo
                  según necesidad del usuario en la vista de líneas de pedidos. 2025.08.02
                
    """,

    'author': "Alconsoft",
    'website': "http://www.alconsoft.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Job Cost',
    'version': '2025.08.02 - 09:00',

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
                'product',
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
        'data/email_templates_jc.xml',
        'views/views_stock_product.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',

    ],
    # Aplicacion:  si aparace cierto (true) esta modulo sera una aplicacion que aprecera en el listado de aplicaciones de odoo.
    'application': True,
}
