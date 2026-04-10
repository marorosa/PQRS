"""Sistema de Gestión de PQRS para Empresas Públicas - Sprint 1: Registro de Ciudadanos"""
import re
import datetime
import bcrypt
import reflex as rx
from .usuario_model import Usuario
from sqlmodel import select
from rxconfig import config
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def tiene_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
def confirmar_contraseña(contraseña: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(contraseña.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False
def validar_correo(correo: str) -> bool:
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", correo))
def cantida_minima_contraseña(contraseña: str) -> bool:
    return len(contraseña) >= 8 and re.search(r'[A-Z]', contraseña) and re.search(r'[a-z]', contraseña) and re.search(r'[0-9]', contraseña) and re.search(r'[@$!%*?&]', contraseña)


def enviar_correo_bienvenida(email_destinatario: str, email_usuario: str):
    """Envía un correo de bienvenida con las credenciales de acceso"""
    try:
        # Obtener credenciales del archivo .env
        email_sender = os.getenv("EMAIL_SENDER")
        email_password = os.getenv("EMAIL_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        empresa_nombre = os.getenv("EMPRESA_NOMBRE", "Sistema de Gestión de PQRS")
        
        # Validar que existan credenciales
        if not email_sender or not email_password:
            print("⚠️ Advertencia: Credenciales de correo no configuradas en .env")
            return False
        
        # Crear mensaje
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = f"¡Bienvenido a {empresa_nombre}!"
        mensaje["From"] = email_sender
        mensaje["To"] = email_destinatario
        
        # Contenido del correo en HTML
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #1e40af; text-align: center;">¡Bienvenido!</h1>
                    <p style="color: #333; font-size: 16px;">Hola,</p>
                    <p style="color: #333; font-size: 16px;">Tu registro en <strong>{empresa_nombre}</strong> ha sido exitoso. A continuación, encontrarás tus datos de acceso:</p>
                    
                    <div style="background-color: #f0f7ff; padding: 15px; border-left: 4px solid #1e40af; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 5px 0;"><strong>📧 Correo:</strong> <code>{email_usuario}</code></p>
                    </div>
                    
                    <p style="color: #333; font-size: 16px;">Para iniciar sesión, ingresa a:</p>
                    <p style="text-align: center; margin: 20px 0;">
                        <a href="http://localhost:3000/login" style="background-color: #1e40af; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Ir a Iniciar Sesión</a>
                    </p>
                    
                    <hr style="border: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #666; font-size: 14px;"><strong>Recuerda:</strong> Nunca compartas tu contraseña con terceros. El equipo de soporte nunca te pedirá tu contraseña.</p>
                    <p style="color: #666; font-size: 14px;">Si tienes preguntas o problemas, contacta a nuestro equipo de soporte.</p>
                    <p style="text-align: center; color: #999; font-size: 12px; margin-top: 30px;">© 2026 {empresa_nombre}. Todos los derechos reservados.</p>
                </div>
            </body>
        </html>
        """
        
        # Adjuntar el contenido
        parte_html = MIMEText(html, "html")
        mensaje.attach(parte_html)
        
        # Enviar correo
        with smtplib.SMTP(smtp_server, smtp_port) as servidor:
            servidor.starttls()
            servidor.login(email_sender, email_password)
            servidor.sendmail(email_sender, email_destinatario, mensaje.as_string())
        
        print(f"✅ Correo enviado exitosamente a {email_destinatario}")
        return True
    
    except Exception as e:
        print(f"❌ Error al enviar correo: {str(e)}")
        return False


print(tiene_password("Hola123"))

class State(rx.State):
    "En esta clase se define el estado de la aplicación, es decir, las variables que se van a usar en la aplicación y sus valores iniciales."
    contraseña: str = ""
    confirmar_contraseña: str = ""
    correo: str = ""
    
    error_de_registro: str = ""
    succes: str = ""
    error_de_contraseña: str = ""
    succes2: str = ""
    
    id_usuario: int = 0
    es_autentica: bool = False
    
    def borrar_mensajes_de_estado(self):
        self.error_de_registro = ""
        self.succes = ""
        self.error_de_contraseña = ""
        self.succes2 = ""
        
    def validacion_de_entradas(self, require_strong_pw: bool = True) -> bool:
        if not validar_correo(self.correo):
            self.error_de_registro = "Correo no válido."
            return False
        if require_strong_pw and not cantida_minima_contraseña(self.contraseña):
            self.error_de_registro = "La contraseña debe tener al menos 8 caracteres, incluyendo mayúsculas, minúsculas, números y caracteres especiales."
            return False
        if require_strong_pw and self.contraseña != self.confirmar_contraseña:
            self.error_de_registro = "Las contraseñas no coinciden."
            return False
        return True
    def signup(self):
        self.borrar_mensajes_de_estado()
        if not self.validacion_de_entradas():
            return
        with rx.session() as session:
            existing_user = session.exec(select(Usuario).where(Usuario.email == self.correo)).first()
            if existing_user:
                self.error_de_registro = "El correo ya está registrado."
                return
            nuevo_usuario = Usuario(email=self.correo, Contraseña=tiene_password(self.contraseña), rol="ciudadano", is_active=True, Fecha_de_creacion=datetime.datetime.now())
            session.add(nuevo_usuario)
            session.commit()
            # Enviar correo de bienvenida
            enviar_correo_bienvenida(self.correo, self.correo)
            self.succes = "Registro exitoso. Revisa tu correo para confirmar. Ahora puedes iniciar sesión."
            self.error_de_registro = ""
            self.contraseña = ""
            self.confirmar_contraseña = ""
    def login(self):
        self.borrar_mensajes_de_estado()
        if not self.validacion_de_entradas(require_strong_pw=False):
            self.succes2 = ""
            return
        with rx.session() as session:
            user = session.exec(select(Usuario).where(Usuario.email == self.correo)).first()
            if not user or not confirmar_contraseña(self.contraseña, user.Contraseña):
                self.error_de_contraseña = "Correo o contraseña incorrectos."
                self.succes2 = ""
                return
            if not user.is_active:
                self.error_de_contraseña = "La cuenta no está activa."
                self.succes2 = ""
                return
            self.id_usuario = user.id
            self.es_autentica = True
            self.succes2 = "Inicio de sesión exitoso."
            self.error_de_contraseña = ""
            self.contraseña = ""
            self.confirmar_contraseña = ""
            return rx.redirect("/dashboard")
    def logout(self):
        "cerrar sesion de usuario"
        self.id_usuario = 0
        self.correo = ""
        self.contraseña = ""
        self.confirmar_contraseña = ""
        self.es_autentica = False
        self.succes2 = "Has cerrado sesión exitosamente."
        self.error_de_contraseña = ""
        return rx.redirect("/")
    """The app state."""


def auth_card(title: str, on_submit, show_confirm: bool = False) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(title, size="2", color="black"),
            rx.input(placeholder="Correo electrónico", type="email", value=State.correo, on_change=State.set_correo, bg="white", border_color="gray.300", width="100%", border_radius="md"),
            rx.input(placeholder="Contraseña", type="password", value=State.contraseña, on_change=State.set_contraseña, bg="white", border_color="gray.300", width="100%", border_radius="md"),
            
            rx.cond(
                show_confirm,
                rx.input(placeholder="Confirmar contraseña", type="password", value=State.confirmar_contraseña, on_change=State.set_confirmar_contraseña, bg="white", border_color="gray.300", width="100%", border_radius="md")
            ),
            
            rx.text(State.error_de_registro, color="red.500", font_size="sm"),
            rx.text(State.error_de_contraseña, color="red.500", font_size="sm"),
            rx.text(State.succes, color="green.500", font_size="sm"),
            rx.text(State.succes2, color="green.500", font_size="sm"),
            
            rx.button(title, on_click=on_submit, width="100%", color_scheme="blue", box_shadow="md", size="4"),
            spacing="4",
            align_items="center",
        ),
        width="100%",
        max_width="450px",
        padding="32px",
        box_shadow="2xl",
        border_radius="xl",
        bg="white"
    )
    # Welcome Page (Index)


def navbar() -> rx.Component:
    return rx.hstack(
        rx.link("Inicio", href="/", font_weight="bold", color="black", text_decoration="none", _hover={"color":"gray.100"}),
        rx.link("Registro de Ciudadano", href="/registro", font_weight="bold", color="black", text_decoration="none", _hover={"color":"gray.100"}),
        rx.link("Iniciar Sesión", href="/login", font_weight="bold", color="black", text_decoration="none", _hover={"color":"gray.100"}),
        spacing="6",
        padding="16px",
        width="100%",
        justify="center",
        bg="blue.600",
        box_shadow="md",
        position="sticky",
        top="0",
        z_index="sticky"
    )


def index() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        navbar(), # Agregamos el menú
        rx.center(
            rx.vstack(
                rx.heading("Sistema de Gestión de PQRS", size="9", color="black"),
                rx.text("Bienvenido al sistema de Peticiones, Quejas, Reclamos y Sugerencias de la empresa pública. Regístrate para enviar tus solicitudes.", size="5", color="black", text_align="center", max_width="780px"),
                rx.link(rx.button("Comenzar", color_scheme="blue", size="4"), href="/registro", mt="6"),
                spacing="5",
                justify="center",
                align_items="center"
            ),
            min_height="84vh",
            width="100%",
            bg_gradient="linear(to-r, blue.50, teal.50)"
        )
    )


def registro_page() -> rx.Component:
    return rx.container(
        navbar(),
        rx.center(
            # Llamamos a auth_card con la función de signup y pidiendo confirmación
            auth_card("Registrarme como Ciudadano", State.signup, show_confirm=True),
            min_height="85vh"
        )
    )

def login_page() -> rx.Component:
    return rx.container(
        navbar(),
        rx.center(
            # Llamamos a auth_card. Nota: en tu código llamaste 'usuario' a la función de login
            auth_card("Iniciar Sesión", State.login,  show_confirm=False),
            min_height="85vh"
        )
    )

def dashboard() -> rx.Component:
    return rx.cond(
        State.es_autentica,
        rx.container(
            navbar(),
            rx.center(
                rx.card(
                    rx.vstack(
                        rx.heading("Panel de Ciudadano", size="8", color="black"),
                        rx.text("¡Bienvenido! Aquí podrás gestionar tus Peticiones, Quejas, Reclamos y Sugerencias.", color="gray.600"),
                        rx.text("Funcionalidad completa próximamente en próximos sprints.", color="gray.500"),
                        rx.button("Cerrar Sesión", on_click=State.logout, color_scheme="red", width="100%"),
                        spacing="4",
                        align_items="center"
                    ),
                    max_width="640px",
                    p="10",
                    box_shadow="2xl",
                    border_radius="2xl"
                ),
                min_height="84vh"
            )
        ),
        rx.container(
            navbar(),
            rx.center(
                rx.vstack(
                    rx.heading("Acceso Denegado", size="8", color="red.500"),
                    rx.text("Necesitas iniciar sesión para acceder a esta página."),
                    rx.link(rx.button("Ir al Login", color_scheme="blue"), href="/login"),
                    spacing="4",
                    align_items="center"
                ),
                min_height="84vh"
            )
        )
    )


app = rx.App()
app.add_page(index, route="/", title="Inicio - Sistema PQRS")
app.add_page(registro_page, route="/registro", title="Registro de Ciudadano")
app.add_page(login_page, route="/login", title="Iniciar Sesión")
app.add_page(dashboard, route="/dashboard", title="Panel de Ciudadano")
