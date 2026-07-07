# -*- coding: utf-8 -*-
{
    "name": "IXC ODOO - Contratos y Firma Digital",
    "version": "19.0.1.0.0",
    "summary": "Integracion IXC Provedor: contratos, firma digital Sign Enterprise y sincronizacion",
    "description": """
        Modulo de integracion entre Odoo 19 Enterprise e IXC Provedor.
        - Gestion de planes de datos/servicios (ixcodoo.data.plan)
        - Contratos con firma digital nativa (Sign Enterprise)
        - Sincronizacion automatica bidireccional con API IXC Provedor
        - Cron horario de verificacion de contratos firmados
        - Panel de configuracion con test de conexion
    """,
    "author": "WEBFIX",
    "website": "https://webfix.com",
    "category": "Sales/Contracts",
    "license": "OPL-1",
    "application": True,
    "installable": True,
    "depends": ["base", "mail", "sign", "sale"],
    "external_dependencies": {
        "python": ["requests"],
    },
    "data": [
        "security/ir.model.access.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "views/data_plan_views.xml",
        "views/contract_plan_views.xml",
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
        "views/menu.xml",
    ],
}
