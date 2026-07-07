# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IxcodooContractPlan(models.Model):
    _name = "ixcodoo.contract.plan"
    _description = "Contrato de Plan IXC"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Referencia",
        readonly=True,
        default=lambda self: _("Nuevo"),
        copy=False,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        required=True,
        tracking=True,
    )
    plan_id = fields.Many2one(
        "ixcodoo.data.plan",
        string="Plan",
        required=True,
        tracking=True,
    )
    customer_name = fields.Char(
        string="Nombre del Cliente",
        related="partner_id.name",
        readonly=True,
    )
    customer_email = fields.Char(
        string="Correo del Cliente",
        related="partner_id.email",
        readonly=True,
    )
    customer_phone = fields.Char(
        string="Telefono del Cliente",
        related="partner_id.phone",
        readonly=True,
    )
    starting_date = fields.Date(string="Fecha Inicio", tracking=True)
    ending_date = fields.Date(string="Fecha Fin", tracking=True)

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("pending", "Pendiente de Firma"),
            ("signed", "Firmado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
        required=True,
    )

    sign_request_id = fields.Many2one(
        "sign.request",
        string="Solicitud de Firma",
        readonly=True,
        copy=False,
    )

    ixc_sync_state = fields.Selection(
        [
            ("not_synced", "No sincronizado"),
            ("synced", "Sincronizado"),
            ("error", "Error"),
        ],
        string="Estado Sync IXC",
        default="not_synced",
        readonly=True,
        copy=False,
    )
    ixc_contract_id = fields.Char(
        string="ID Contrato IXC",
        readonly=True,
        copy=False,
        help="ID del contrato creado en IXC Provedor",
    )
    ixc_last_sync = fields.Datetime(
        string="Ultima Sincronizacion",
        readonly=True,
        copy=False,
    )

    notes = fields.Html(string="Notas")

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("Nuevo")) == _("Nuevo"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ixcodoo.contract.plan"
                ) or _("Nuevo")
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # Acciones de flujo
    # -------------------------------------------------------------------------
    def action_request_signature(self):
        """
        Envia el contrato a firma digital usando Sign Enterprise.
        Busca automaticamente la plantilla 'Contrato de Plan - IXCODOO' en
        el modulo Sign de Odoo Enterprise.
        NOTA: El usuario administrador debe crear manualmente esta plantilla
        en la app Sign (Enterprise) antes de usar este boton.
        """
        self.ensure_one()
        if not self.plan_id:
            raise UserError(_("Debe seleccionar un plan antes de enviar a firma."))
        if not self.partner_id.email:
            raise UserError(
                _("El cliente debe tener un correo electronico configurado.")
            )

        sign_template = self.env["sign.template"].search(
            [("name", "=", "Contrato de Plan - IXCODOO")], limit=1
        )
        if not sign_template:
            raise UserError(
                _(
                    "No se encontro la plantilla 'Contrato de Plan - IXCODOO' en Sign.\n"
                    "El administrador debe crearla manualmente en el modulo Sign "
                    "(Enterprise) antes de usar este boton."
                )
            )

        sign_request = self.env["sign.request"].create({
            "template_id": sign_template.id,
            "reference": "Contrato %s - %s" % (self.name, self.partner_id.name),
            "request_item_ids": [(0, 0, {
                "partner_id": self.partner_id.id,
                "role_id": self.env.ref("sign.sign_item_role_customer").id,
            })],
        })
        sign_request.action_sent()

        self.write({
            "sign_request_id": sign_request.id,
            "state": "pending",
        })
        self.message_post(body=_("Solicitud de firma enviada al cliente."))
        return True

    def action_sync_to_ixc(self):
        """
        Sincroniza el contrato firmado con IXC Provedor.
        AJUSTAR nombres de campos segun documentacion oficial:
        https://wikiapiprovedor.ixcsoft.com.br/
        """
        self.ensure_one()
        ixc_client = self.env["ixcodoo.ixc.client"]

        try:
            # 1. Crear/actualizar cliente en IXC
            partner_data = {
                "razao": self.partner_id.name,
                "cnpj_cpf": self.partner_id.vat or "",
                "email": self.partner_id.email or "",
                "telefone_celular": self.partner_id.phone or "",
            }
            ixc_client.create_or_update_cliente(partner_data)

            # 2. Crear/actualizar contrato en IXC
            contract_data = {
                "id_cliente": self.partner_id.ixc_contract_id or "",
                "id_plano": self.plan_id.ixc_plan_id or "",
                "data_inicio": str(self.starting_date) if self.starting_date else "",
                "data_final": str(self.ending_date) if self.ending_date else "",
                "status": "A",
            }
            result = ixc_client.create_or_update_contrato(contract_data)

            vals = {
                "ixc_sync_state": "synced",
                "ixc_last_sync": fields.Datetime.now(),
            }
            if result and result.get("id"):
                vals["ixc_contract_id"] = str(result["id"])
            self.write(vals)

            # Actualizar partner con datos del contrato
            self.partner_id.write({
                "ixcodoo_plan_id": self.plan_id.id,
                "ixcodoo_contract_state": "active",
                "ixcodoo_contract_start": self.starting_date,
                "ixcodoo_contract_end": self.ending_date,
            })

            self.message_post(body=_("Contrato sincronizado exitosamente con IXC."))

        except Exception as e:
            _logger.exception("Error al sincronizar contrato %s con IXC", self.name)
            self.write({
                "ixc_sync_state": "error",
                "ixc_last_sync": fields.Datetime.now(),
            })
            self.message_post(
                body=_("Error al sincronizar con IXC: %s") % str(e)
            )
            raise UserError(
                _("Error al sincronizar con IXC: %s") % str(e)
            ) from e

    def action_cancel(self):
        """Cancela el contrato."""
        self.ensure_one()
        self.write({"state": "cancelled"})
        if self.partner_id.ixcodoo_plan_id == self.plan_id:
            self.partner_id.write({"ixcodoo_contract_state": "cancelled"})
        self.message_post(body=_("Contrato cancelado."))

    def action_reset_to_draft(self):
        """Regresa el contrato a borrador."""
        self.ensure_one()
        self.write({"state": "draft"})

    # -------------------------------------------------------------------------
    # Cron: verificar contratos firmados
    # -------------------------------------------------------------------------
    @api.model
    def _cron_check_signed_contracts(self):
        """
        Cron ejecutado cada hora.
        Busca contratos en estado 'pending' cuya solicitud de firma
        ya fue completada (sign_request_id.state == 'signed') y los
        pasa a 'signed', ejecutando la sincronizacion con IXC.
        """
        pending_contracts = self.search([
            ("state", "=", "pending"),
            ("sign_request_id", "!=", False),
        ])
        for contract in pending_contracts:
            if contract.sign_request_id.state == "signed":
                _logger.info(
                    "Contrato %s firmado detectado por cron, sincronizando...",
                    contract.name,
                )
                contract.write({"state": "signed"})
                try:
                    contract.action_sync_to_ixc()
                except Exception:
                    _logger.exception(
                        "Error en cron al sincronizar contrato %s",
                        contract.name,
                    )
