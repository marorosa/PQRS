import reflex as rx

config = rx.Config(
    app_name="autenticacion",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)