# Custom Addons — Odoo 20.0 (UNICAH)

- **Estudiante:** Luis Medina
- **Número de cuenta:** 0806200300590

## Módulo `ventas_unicah`
Personalización del módulo de Ventas en Odoo 20.0:
- **Etapa 1 y 2:** Campo `canal_preferido` (*Tienda*, *Teléfono*, *Sitio web*, *Distribuidor*) en contactos (`res.partner`) y en las vistas de formulario y lista (`base.view_partner_form` y `base.view_partner_tree`).
- **Etapa 3:** Campos calculados `canal_venta`, `total_unidades` y `requiere_aprobacion` (`> 50,000`) en pedidos de venta (`sale.order`), con vistas de formulario, lista (`sum="Total"`) y filtros/agrupación en búsqueda.
- **Etapa 4:** Regla de negocio de aprobación de pedidos mayores a `50,000` por un administrador de ventas (`sales_team.group_sale_manager`), botón **Aprobar** y alerta amarilla.
- **Retos adicionales:** Anulación automática de `aprobado_por` al cambiar `amount_total`, restricción de canal *Distribuidor* únicamente para empresas (`is_company`), y columna *Canal preferido* en la lista de clientes.

## Despliegue gratuito en la nube (Render.com)
Este repositorio incluye los archivos listos para desplegar Odoo 20.0 + `ventas_unicah` en **Render.com (plan gratuito)** conectado a PostgreSQL gratuito:
- `Dockerfile`: Empaqueta `odoo:20.0` junto con `ventas_unicah` y el script de arranque.
- `entrypoint_cloud.py`: Configura dinámicamente Odoo desde `DATABASE_URL` y `PORT`, inicializa la base de datos e instala `ventas_unicah` en el primer arranque, crea los datos de prueba y configura el usuario administrador de revisión (`revisor@unicah.edu`).
- `render.yaml`: Blueprint de Render para crear en un solo paso la base de datos PostgreSQL gratuita (`odoo20-db`) y el Web Service Docker gratuito (`odoo20-unicah`).

### Pasos rápidos en Render.com
1. Entra a [https://dashboard.render.com](https://dashboard.render.com) e inicia sesión con tu cuenta de GitHub.
2. Haz clic en **New + > Blueprint** (o crea primero un **PostgreSQL** gratuito y luego un **Web Service** con entorno Docker conectado a `LuisMedina420/odoo20`).
3. Si usas **Blueprint**, selecciona el repositorio `LuisMedina420/odoo20` y confirma la creación de `odoo20-db` y `odoo20-unicah`.
4. Si lo creas manualmente:
   - Crea una base de datos **PostgreSQL** (plan **Free**) o en **Neon.tech** (plan **Free**) y copia su **Internal Database URL** (o connection string).
   - Crea un **Web Service** (plan **Free**, Language: **Docker**) conectado a `LuisMedina420/odoo20`.
   - En **Environment Variables**, agrega `DATABASE_URL` con la URL de conexión y `ODOO_ADMIN_PASSWORD` con `Unicah2026*`.
5. Al terminar el primer arranque, abre la URL pública `.onrender.com` e inicia sesión con:
   - **Usuario:** `revisor@unicah.edu`
   - **Contraseña:** `Unicah2026*`
