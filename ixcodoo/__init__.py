# -*- coding: utf-8 -*-
from . import models
try:
    from . import services
except ImportError:
    import logging
    _logger = logging.getLogger(__name__)
    _logger.warning("No se pudo importar services (posiblemente falta 'requests'). "
                    "La sincronizacion con IXC no estara disponible hasta instalar el paquete.")
