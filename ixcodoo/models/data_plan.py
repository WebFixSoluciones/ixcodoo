# -*- coding: utf-8 -*-
from odoo import models, fields


class IxcodooDataPlan(models.Model):
    _name = "ixcodoo.data.plan"
    _description = "Plan de Datos / Servicio IXC"
    _order = "name"

    name = fields.Char(string="Nombre del Plan", required=True)
    price = fields.Float(string="Precio", digits="Product Price", required=True)
    duration_months = fields.Integer(string="Duracion (meses)", default=12)
    ixc_plan_id = fields.Char(
        string="ID Plan IXC",
        help="Identificador del plan en el sistema IXC Provedor. "
             "AJUSTAR segun documentacion oficial: https://wikiapiprovedor.ixcsoft.com.br/",
    )
    active = fields.Boolean(default=True)
