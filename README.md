# Custom Addons — Odoo 20.0 (UNICAH)

- **Estudiante:** Luis Medina
- **Número de cuenta:** 0806200300590

## Módulo `ventas_unicah`
Personalización del módulo de Ventas en Odoo 20.0:
- **Etapa 1 y 2:** Campo `canal_preferido` (*Tienda*, *Teléfono*, *Sitio web*, *Distribuidor*) en contactos (`res.partner`) y en las vistas de formulario y lista (`base.view_partner_form` y `base.view_partner_tree`).
- **Etapa 3:** Campos calculados `canal_venta`, `total_unidades` y `requiere_aprobacion` (`> 50,000`) en pedidos de venta (`sale.order`), con vistas de formulario, lista (`sum="Total"`) y filtros/agrupación en búsqueda.
- **Etapa 4:** Regla de negocio de aprobación de pedidos mayores a `50,000` por un administrador de ventas (`sales_team.group_sale_manager`), botón **Aprobar** y alerta amarilla.
- **Retos adicionales:** Anulación automática de `aprobado_por` al cambiar `amount_total`, restricción de canal *Distribuidor* únicamente para empresas (`is_company`), y columna *Canal preferido* en la lista de clientes.
