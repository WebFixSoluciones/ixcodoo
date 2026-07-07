# -*- coding: utf-8 -*-
"""
Servicio cliente para la API de IXC Provedor.
AJUSTAR NOMBRES DE CAMPOS SEGUN DOCUMENTACION OFICIAL:
https://wikiapiprovedor.ixcsoft.com.br/

Este AbstractModel centraliza todas las llamadas HTTP a la API IXC.
"""
import base64
import logging

import requests
from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IxcClient(models.AbstractModel):
    _name = "ixcodoo.ixc.client"
    _description = "Cliente API IXC Provedor"

    # -------------------------------------------------------------------------
    # Configuracion
    # -------------------------------------------------------------------------
    def _get_config(self):
        """Lee la configuracion IXC desde ir.config_parameter con sudo()."""
        ICP = self.env["ir.config_parameter"].sudo()
        base_url = ICP.get_param("ixcodoo.base_url", "").rstrip("/")
        token = ICP.get_param("ixcodoo.api_token", "")

        if not base_url or not token:
            raise UserError(
                _(
                    "La integracion con IXC no esta configurada.\n"
                    "Vaya a Ajustes > Integracion IXC y configure "
                    "la URL y el Token."
                )
            )
        return base_url, token

    def _get_headers(self, token):
        """
        Construye headers con Authorization: Basic base64(token + ':').
        La API IXC usa autenticacion HTTP Basic donde el token va como
        usuario, sin contrasena.
        """
        auth_str = base64.b64encode(("%s:" % token).encode()).decode()
        return {
            "Authorization": "Basic %s" % auth_str,
            "Content-Type": "application/json",
        }

    # -------------------------------------------------------------------------
    # Metodo generico de peticion
    # -------------------------------------------------------------------------
    def _api_request(self, method, endpoint, data=None):
        """
        Realiza una peticion HTTP a la API IXC.
        AJUSTAR endpoints segun documentacion oficial:
        https://wikiapiprovedor.ixcsoft.com.br/
        https://wiki.ixcsoft.com.br/pt-br/API
        """
        base_url, token = self._get_config()
        headers = self._get_headers(token)
        url = "%s/webservice/v1/%s" % (base_url, endpoint)

        try:
            response = requests.request(
                method,
                url,
                json=data,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.ConnectionError:
            _logger.error("No se pudo conectar con IXC: %s", url)
            raise UserError(
                _("No se pudo conectar con el servidor IXC. Verifique la URL.")
            )
        except requests.exceptions.Timeout:
            _logger.error("Timeout al conectar con IXC: %s", url)
            raise UserError(
                _("Tiempo de espera agotado al conectar con IXC.")
            )
        except requests.exceptions.HTTPError as e:
            _logger.error("Error HTTP de IXC: %s - %s", e, url)
            raise UserError(
                _("Error HTTP al comunicarse con IXC: %s") % str(e)
            )
        except Exception as e:
            _logger.exception("Error inesperado al comunicarse con IXC")
            raise UserError(
                _("Error inesperado al comunicarse con IXC: %s") % str(e)
            )

    # -------------------------------------------------------------------------
    # Endpoints IXC
    # -------------------------------------------------------------------------
    def create_or_update_cliente(self, partner_data):
        """
        Crea o actualiza un cliente en IXC Provedor.
        AJUSTAR NOMBRES DE CAMPOS SEGUN DOCUMENTACION OFICIAL:
        https://wikiapiprovedor.ixcsoft.com.br/

        Args:
            partner_data (dict): Datos del cliente. Ejemplo esperado:
                {
                    "razao": "Nombre del Cliente",
                    "cnpj_cpf": "12345678901",
                    "email": "cliente@email.com",
                    "telefone_celular": "+5511999999999",
                }
        Returns:
            dict: Respuesta de la API IXC.
        """
        _logger.info(
            "Creando/actualizando cliente en IXC: %s",
            partner_data.get("razao", ""),
        )
        return self._api_request("POST", "cliente", data=partner_data)

    def create_or_update_contrato(self, contract_data):
        """
        Crea o actualiza un contrato en IXC Provedor.
        AJUSTAR NOMBRES DE CAMPOS SEGUN DOCUMENTACION OFICIAL:
        https://wikiapiprovedor.ixcsoft.com.br/

        Args:
            contract_data (dict): Datos del contrato. Ejemplo esperado:
                {
                    "id_cliente": "123",
                    "id_plano": "456",
                    "data_inicio": "2026-01-01",
                    "data_final": "2027-01-01",
                    "status": "A",
                }
        Returns:
            dict: Respuesta de la API IXC con el ID del contrato creado.
        """
        _logger.info(
            "Creando/actualizando contrato en IXC para cliente: %s",
            contract_data.get("id_cliente", ""),
        )
        return self._api_request("POST", "cliente_contrato", data=contract_data)
