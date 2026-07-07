# -*- coding: utf-8 -*-
import base64
import logging

from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ixcodoo_base_url = fields.Char(
        string="URL Base IXC",
        config_parameter="ixcodoo.base_url",
        help="URL base de la API IXC Provedor, ej: https://miempresa.ixcsoft.com.br",
    )
    ixcodoo_api_token = fields.Char(
        string="Token API IXC",
        config_parameter="ixcodoo.api_token",
        help="Token de autenticacion para la API IXC Provedor",
    )

    def action_test_ixc_connection(self):
        """
        Prueba la conexion con la API IXC usando HTTP Basic Auth.
        El token se envia como usuario, sin contrasena (base64(token:)).
        """
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param(
            "ixcodoo.base_url", ""
        ).rstrip("/")
        token = self.env["ir.config_parameter"].sudo().get_param(
            "ixcodoo.api_token", ""
        )

        if not base_url or not token:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error de configuracion"),
                    "message": _("Debe configurar la URL base y el token API."),
                    "type": "danger",
                    "sticky": False,
                },
            }

        import requests

        try:
            auth_str = base64.b64encode(("%s:" % token).encode()).decode()
            headers = {
                "Authorization": "Basic %s" % auth_str,
                "Content-Type": "application/json",
            }
            url = "%s/webservice/v1/cliente" % base_url
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Conexion exitosa"),
                    "message": _(
                        "Conexion con IXC establecida correctamente (HTTP %s)."
                    ) % response.status_code,
                    "type": "success",
                    "sticky": False,
                },
            }

        except requests.exceptions.ConnectionError:
            msg = _("No se pudo conectar con el servidor IXC. Verifique la URL.")
        except requests.exceptions.Timeout:
            msg = _("Tiempo de espera agotado al conectar con IXC.")
        except requests.exceptions.HTTPError as e:
            msg = _("Error HTTP al conectar con IXC: %s") % str(e)
        except Exception as e:
            msg = _("Error inesperado: %s") % str(e)

        _logger.warning("Test de conexion IXC fallido: %s", msg)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Error de conexion"),
                "message": msg,
                "type": "danger",
                "sticky": False,
            },
        }
