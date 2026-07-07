# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    ixcodoo_plan_id = fields.Many2one(
        "ixcodoo.data.plan",
        string="Plan Contratado",
        tracking=True,
    )
    ixcodoo_contract_state = fields.Selection(
        [
            ("none", "Sin contrato"),
            ("active", "Activo"),
            ("expired", "Expirado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado Contrato",
        default="none",
        tracking=True,
    )
    ixcodoo_contract_start = fields.Date(
        string="Inicio Contrato",
        tracking=True,
    )
    ixcodoo_contract_end = fields.Date(
        string="Fin Contrato",
        tracking=True,
    )

    ixc_contract_id = fields.Char(
        string="ID Contrato IXC",
        readonly=True,
        copy=False,
    )

    ixcodoo_contract_ids = fields.One2many(
        "ixcodoo.contract.plan",
        "partner_id",
        string="Contratos IXCODOO",
    )
    ixcodoo_contract_count = fields.Integer(
        string="Nº Contratos",
        compute="_compute_ixcodoo_contract_count",
    )

    @api.depends("ixcodoo_contract_ids")
    def _compute_ixcodoo_contract_count(self):
        for partner in self:
            partner.ixcodoo_contract_count = len(partner.ixcodoo_contract_ids)
