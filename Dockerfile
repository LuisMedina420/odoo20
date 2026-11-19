FROM odoo:20.0

USER root

COPY ./ventas_unicah /mnt/extra-addons/ventas_unicah
COPY ./entrypoint_cloud.py /entrypoint_cloud.py

RUN chown -R odoo:odoo /mnt/extra-addons/ventas_unicah \
    && chmod -R a+rX /mnt/extra-addons/ventas_unicah \
    && chmod 755 /entrypoint_cloud.py

USER odoo

EXPOSE 8069

ENTRYPOINT ["python3", "/entrypoint_cloud.py"]
