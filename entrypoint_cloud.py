import os
import re
import subprocess
import sys
import time
from urllib.parse import parse_qs, unquote, urlparse

import psycopg2

CONF_PATH = "/tmp/odoo.conf"
ADDONS_PATH = "/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons"


def _conf_escape(value: str) -> str:
    return value.replace("%", "%%")


def get_db_config():
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        parsed = urlparse(database_url)
        query = parse_qs(parsed.query)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "user": unquote(parsed.username or "odoo"),
            "password": unquote(parsed.password or ""),
            "name": parsed.path.lstrip("/") or "odoo",
            "sslmode": query.get("sslmode", [os.environ.get("DB_SSLMODE", "prefer")])[0],
        }

    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "user": os.environ.get("DB_USER", "odoo"),
        "password": os.environ.get("DB_PASSWORD", "odoo"),
        "name": os.environ.get("DB_NAME", "odoo"),
        "sslmode": os.environ.get("DB_SSLMODE", "prefer"),
    }


def write_odoo_conf(db, port: int, admin_password: str) -> None:
    db_regex = f"^{re.escape(db['name'])}$"
    content = "\n".join([
        "[options]",
        f"addons_path = {ADDONS_PATH}",
        f"admin_passwd = {_conf_escape(admin_password)}",
        "data_dir = /var/lib/odoo",
        f"db_host = {db['host']}",
        f"db_port = {db['port']}",
        f"db_user = {_conf_escape(db['user'])}",
        f"db_password = {_conf_escape(db['password'])}",
        f"db_name = {db['name']}",
        f"db_system = {db['name']}",
        f"db_sslmode = {db['sslmode']}",
        f"dbfilter = {db_regex}",
        "db_maxconn = 16",
        "http_interface = 0.0.0.0",
        f"http_port = {port}",
        "proxy_mode = True",
        "list_db = False",
        "with_demo = False",
        "max_cron_threads = 1",
        "workers = 0",
        "",
    ])
    with open(CONF_PATH, "w", encoding="utf-8") as fh:
        fh.write(content)
    os.chmod(CONF_PATH, 0o600)


def wait_for_postgres(db, max_attempts: int = 30) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(
                host=db["host"],
                port=db["port"],
                user=db["user"],
                password=db["password"],
                dbname=db["name"],
                sslmode=db["sslmode"],
                connect_timeout=5,
            )
            conn.close()
            print(f"[cloud-init] Conectado a PostgreSQL ({db['host']}:{db['port']}/{db['name']})", flush=True)
            return
        except psycopg2.OperationalError as exc:
            print(f"[cloud-init] Esperando a PostgreSQL ({attempt}/{max_attempts}): {exc}", flush=True)
            time.sleep(2)
    raise RuntimeError("No se pudo conectar a PostgreSQL después de varios intentos.")


def check_db_status(db):
    conn = psycopg2.connect(
        host=db["host"],
        port=db["port"],
        user=db["user"],
        password=db["password"],
        dbname=db["name"],
        sslmode=db["sslmode"],
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.ir_module_module');")
            has_modules_table = cur.fetchone()[0] is not None
            if not has_modules_table:
                return False, False
            cur.execute("SELECT state FROM ir_module_module WHERE name = 'ventas_unicah';")
            row = cur.fetchone()
            ventas_installed = bool(row and row[0] == "installed")
            return True, ventas_installed
    finally:
        conn.close()


def bootstrap_users_and_demo_data(db_name: str, admin_password: str) -> None:
    setup_script = f"""
admin_pw = {admin_password!r}

# 1. Actualizar contrasena del usuario admin principal
admin_user = env.ref("base.user_admin", raise_if_not_found=False) or env["res.users"].search([("login", "=", "admin")], limit=1)
if admin_user:
    admin_user.sudo().write({{"password": admin_pw}})

# 2. Crear usuario administrador dedicado para revision
grp_user = env.ref("base.group_user")
grp_system = env.ref("base.group_system")
grp_sale_manager = env.ref("sales_team.group_sale_manager")

revisor = env["res.users"].search([("login", "=", "revisor@unicah.edu")], limit=1)
if not revisor:
    revisor = env["res.users"].create({{
        "name": "Revisor UNICAH",
        "login": "revisor@unicah.edu",
        "email": "revisor@unicah.edu",
        "password": admin_pw,
        "group_ids": [(6, 0, [grp_user.id, grp_system.id, grp_sale_manager.id])],
    }})
else:
    revisor.sudo().write({{
        "password": admin_pw,
        "group_ids": [(6, 0, [grp_user.id, grp_system.id, grp_sale_manager.id])],
    }})

# 3. Crear clientes de prueba del proyecto trabajado en clase
Partner = env["res.partner"]
p_tel = Partner.search([("name", "=", "Cliente Prueba (Canal Teléfono)")], limit=1)
if not p_tel:
    p_tel = Partner.create({{
        "name": "Cliente Prueba (Canal Teléfono)",
        "canal_preferido": "telefono",
        "customer_rank": 1,
    }})

p_tienda = Partner.search([("name", "=", "Cliente Prueba (Canal Tienda)")], limit=1)
if not p_tienda:
    p_tienda = Partner.create({{
        "name": "Cliente Prueba (Canal Tienda)",
        "canal_preferido": "tienda",
        "customer_rank": 1,
    }})

p_dist = Partner.search([("name", "=", "Distribuidora Honduras S.A.")], limit=1)
if not p_dist:
    p_dist = Partner.create({{
        "name": "Distribuidora Honduras S.A.",
        "is_company": True,
        "canal_preferido": "distribuidor",
        "customer_rank": 1,
    }})

# 4. Crear producto Laptop (30,000) y cotizaciones de prueba si no existen
Product = env["product.template"]
laptop = Product.search([("name", "=", "Laptop")], limit=1)
if not laptop:
    laptop = Product.create({{
        "name": "Laptop",
        "list_price": 30000.0,
    }})

SaleOrder = env["sale.order"]
if SaleOrder.search_count([]) == 0:
    SaleOrder.create({{
        "partner_id": p_tel.id,
        "order_line": [(0, 0, {{
            "product_id": laptop.product_variant_id.id,
            "product_uom_qty": 3.0,
        }})],
    }})
    SaleOrder.create({{
        "partner_id": p_tienda.id,
        "order_line": [(0, 0, {{
            "product_id": laptop.product_variant_id.id,
            "product_uom_qty": 1.0,
        }})],
    }})

env.cr.commit()
print("[cloud-init] Usuario revisor@unicah.edu y datos iniciales configurados.")
"""
    proc = subprocess.run(
        ["odoo", "shell", "-c", CONF_PATH, "-d", db_name, "--no-http"],
        input=setup_script,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"odoo shell finalizó con código {proc.returncode}")


def main() -> None:
    db = get_db_config()
    port = int(os.environ.get("PORT", "8069"))
    admin_password = os.environ.get("ODOO_ADMIN_PASSWORD", "Unicah2026*")

    write_odoo_conf(db, port, admin_password)
    wait_for_postgres(db)

    has_modules_table, ventas_installed = check_db_status(db)
    if not has_modules_table:
        print(f"[cloud-init] Inicializando base de datos {db['name']} con base y ventas_unicah...", flush=True)
        subprocess.run(
            ["odoo", "-c", CONF_PATH, "-d", db["name"], "-i", "base,ventas_unicah", "--stop-after-init"],
            check=True,
        )
        bootstrap_users_and_demo_data(db["name"], admin_password)
    elif not ventas_installed:
        print(f"[cloud-init] Instalando ventas_unicah en {db['name']}...", flush=True)
        subprocess.run(
            ["odoo", "-c", CONF_PATH, "-d", db["name"], "-i", "ventas_unicah", "--stop-after-init"],
            check=True,
        )
        bootstrap_users_and_demo_data(db["name"], admin_password)
    else:
        print(f"[cloud-init] Base de datos {db['name']} ya inicializada con ventas_unicah.", flush=True)

    print(f"[cloud-init] Iniciando servidor Odoo 20 en 0.0.0.0:{port}...", flush=True)
    os.execvp("odoo", ["odoo", "-c", CONF_PATH, "-d", db["name"]])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[cloud-init] ERROR FATAL: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
