"""Sistema de Gestión de PQRS para Empresas Públicas - Sprint 1: Registro de Ciudadanos"""
import re
import datetime
from datetime import datetime
import bcrypt
import base64
import uuid
import reflex as rx
from .usuario_model import Usuario
from sqlmodel import select
from rxconfig import config
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
# Carpeta donde se guardarán los archivos subidos por los usuarios
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
from typing import List, Dict

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
    # Requiere: al menos 8 caracteres, una mayúscula, una minúscula,
    # un número y al menos un carácter especial (cualquier signo de puntuación).
    return (
        len(contraseña) >= 8
        and re.search(r'[A-Z]', contraseña)
        and re.search(r'[a-z]', contraseña)
        and re.search(r'[0-9]', contraseña)
        and re.search(r'[^\w\s]', contraseña) is not None
    )


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


# quitar prints de prueba

class State(rx.State):
    "En esta clase se define el estado de la aplicación, es decir, las variables que se van a usar en la aplicación y sus valores iniciales."
    contraseña: str = ""
    confirmar_contraseña: str = ""
    correo: str = ""
    tipo_solicitud: str = ""
    asunto: str = ""
    descripcion: str = ""
    ubicacion: str = ""
    documento: str = ""
    solicitudes: List[Dict] = []
    editar_solicitud_id: int = 0
    solicitud_mensaje: str = ""
    
    error_de_registro: str = ""
    succes: str = ""
    error_de_contraseña: str = ""
    succes2: str = ""
    
    id_usuario: int = 0
    es_autentica: bool = False
    show_password: bool = False
    # Campos para cambiar contraseña
    current_password: str = ""
    new_password: str = ""
    confirm_new_password: str = ""
    change_pw_message: str = ""
    
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
            hashed = tiene_password(self.contraseña)
            nuevo_usuario = Usuario(email=self.correo, Contraseña=hashed, rol="ciudadano", is_active=True, Fecha_de_creacion=datetime.now())
            session.add(nuevo_usuario)
            session.commit()
            print(f"Usuario registrado: {self.correo}")
            # Enviar correo de bienvenida
            enviar_correo_bienvenida(self.correo, self.correo)
            self.succes = "Registro exitoso. Revisa tu correo para confirmar. Ahora puedes iniciar sesión."
            self.error_de_registro = ""
            self.contraseña = ""
            self.confirmar_contraseña = ""
            self.show_password = False
    def login(self):
        self.borrar_mensajes_de_estado()
        if not self.validacion_de_entradas(require_strong_pw=False):
            self.succes2 = ""
            return
        with rx.session() as session:
            user = session.exec(select(Usuario).where(Usuario.email == self.correo)).first()
            pw_ok = False
            try:
                pw_ok = confirmar_contraseña(self.contraseña, user.Contraseña) if user else False
            except Exception as e:
                print(f"Error comprobando contraseña: {e}")
            print(f"Login attempt for: {self.correo}, success: {pw_ok}")
            if not user or not pw_ok:
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
            self.show_password = False
            return rx.redirect("/solicitudes")
    def logout(self):
        "cerrar sesion de usuario"
        self.id_usuario = 0
        self.correo = ""
        self.contraseña = ""
        self.confirmar_contraseña = ""
        self.es_autentica = False
        self.show_password = False
        self.succes2 = "Has cerrado sesión exitosamente."
        self.error_de_contraseña = ""
        return rx.redirect("/")

    def change_password(self):
        """Cambiar la contraseña del usuario autenticado."""
        self.change_pw_message = ""
        if not self.es_autentica or not self.id_usuario:
            self.change_pw_message = "Debes iniciar sesión para cambiar la contraseña."
            return
        # Validaciones básicas
        if not self.current_password or not self.new_password or not self.confirm_new_password:
            self.change_pw_message = "Completa todos los campos."
            return
        if self.new_password != self.confirm_new_password:
            self.change_pw_message = "La nueva contraseña y su confirmación no coinciden."
            return
        if not cantida_minima_contraseña(self.new_password):
            self.change_pw_message = "La nueva contraseña no cumple los requisitos de seguridad."
            return
        with rx.session() as session:
            user = session.exec(select(Usuario).where(Usuario.id == self.id_usuario)).first()
            if not user:
                self.change_pw_message = "Usuario no encontrado."
                return
            try:
                if not confirmar_contraseña(self.current_password, user.Contraseña):
                    self.change_pw_message = "La contraseña actual es incorrecta."
                    return
            except Exception as e:
                self.change_pw_message = f"Error comprobando contraseña: {e}"
                return
            # Actualizar contraseña
            user.Contraseña = tiene_password(self.new_password)
            session.add(user)
            session.commit()
            self.change_pw_message = "Contraseña cambiada correctamente."
            # Limpiar campos
            self.current_password = ""
            self.new_password = ""
            self.confirm_new_password = ""

    def toggle_show_password(self):
        self.show_password = not self.show_password

    def limpiar_formulario_solicitud(self):
        self.tipo_solicitud = ""
        self.asunto = ""
        self.descripcion = ""
        self.ubicacion = ""
        self.documento = ""
        self.editar_solicitud_id = 0
        self.solicitud_mensaje = ""

    def crear_solicitud(self):
        self.solicitud_mensaje = ""
        if not self.tipo_solicitud or not self.asunto or not self.descripcion:
            self.solicitud_mensaje = "Completa los campos obligatorios antes de enviar."
            return
        if self.editar_solicitud_id:
            for solicitud in self.solicitudes:
                if solicitud["id"] == self.editar_solicitud_id:
                    solicitud.update({
                        "tipo_solicitud": self.tipo_solicitud,
                        "asunto": self.asunto,
                        "descripcion": self.descripcion,
                        "ubicacion": self.ubicacion,
                        "documento": self.documento,
                        "estado": "Actualizada",
                    })
                    self.solicitud_mensaje = "Solicitud actualizada con éxito."
                    break
            self.editar_solicitud_id = 0
        else:
            nuevo_id = max([s["id"] for s in self.solicitudes], default=0) + 1
            # Procesar y guardar el archivo adjunto si viene en self.documento
            documento_guardado = ""
            if self.documento:
                try:
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    # Caso: data URL (base64)
                    if isinstance(self.documento, str) and self.documento.startswith("data:"):
                        header, b64 = self.documento.split(",", 1)
                        mime = header.split(";")[0].split(":")[1] if ":" in header else ""
                        ext = mime.split("/")[-1] if "/" in mime else "bin"
                        saved_name = f"adjunto_{uuid.uuid4().hex}.{ext}"
                        path = os.path.join(UPLOAD_DIR, saved_name)
                        with open(path, "wb") as f:
                            f.write(base64.b64decode(b64))
                        documento_guardado = path
                    # Caso: objeto con 'content' y 'name'
                    elif isinstance(self.documento, dict) and "content" in self.documento:
                        content = self.documento.get("content")
                        name = self.documento.get("name", f"adjunto_{uuid.uuid4().hex}")
                        if isinstance(content, str) and content.startswith("data:"):
                            _, b64 = content.split(",", 1)
                            data = base64.b64decode(b64)
                        else:
                            data = base64.b64decode(content)
                        path = os.path.join(UPLOAD_DIR, name)
                        with open(path, "wb") as f:
                            f.write(data)
                        documento_guardado = path
                    else:
                        # Si viene solo el nombre o ruta, lo conservamos tal cual
                        documento_guardado = str(self.documento)
                except Exception as e:
                    self.solicitud_mensaje = f"Error guardando documento: {e}"
                    return

            self.solicitudes.append({
                "id": nuevo_id,
                "tipo_solicitud": self.tipo_solicitud,
                "asunto": self.asunto,
                "descripcion": self.descripcion,
                "ubicacion": self.ubicacion,
                "documento": documento_guardado,
                "estado": "Radicada",
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
            self.solicitud_mensaje = "Solicitud registrada correctamente."
        self.limpiar_formulario_solicitud()

    def editar_solicitud(self, solicitud_id: int):
        solicitud = next((s for s in self.solicitudes if s["id"] == solicitud_id), None)
        if solicitud:
            self.editar_solicitud_id = solicitud_id
            self.tipo_solicitud = solicitud["tipo_solicitud"]
            self.asunto = solicitud["asunto"]
            self.descripcion = solicitud["descripcion"]
            self.ubicacion = solicitud["ubicacion"]
            self.documento = solicitud["documento"]
            self.solicitud_mensaje = "Editando solicitud. Actualiza los campos y guarda cambios."

    def eliminar_solicitud(self, solicitud_id: int):
        self.solicitudes = [s for s in self.solicitudes if s["id"] != solicitud_id]
        self.solicitud_mensaje = "Solicitud eliminada correctamente."

    """The app state."""


def auth_card(title: str, on_submit, show_confirm: bool = False) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(
                title, 
                size="7", 
                color="black", 
                margin_bottom="1em"
            ),
            
            # Input de Correo
            rx.input(
                placeholder="Correo electrónico",
                type="email",
                value=State.correo,
                on_change=State.set_correo,
                bg="white",
                color="black",
                border="1px solid #718096",
                _placeholder={
                    "color": "#718096",
                    "opacity": "1"
                },
                width="100%",
                border_radius="md",
            ),

            # Input de Contraseña
            rx.hstack(
                rx.cond(
                    State.show_password,
                    rx.input(
                        placeholder="Contraseña", 
                        type="text", 
                        value=State.contraseña, 
                        on_change=State.set_contraseña, 
                        bg="white",
                        color="black",
                        border="1px solid #718096",
                        _placeholder={"color": "#718096"},
                        width="100%", 
                        border_radius="md"
                    ),
                    rx.input(
                        placeholder="Contraseña", 
                        type="password", 
                        value=State.contraseña, 
                        on_change=State.set_contraseña, 
                        bg="white",
                        color="black",
                        border="1px solid #718096",
                        _placeholder={"color": "#718096"},
                        width="100%", 
                        border_radius="md"
                    )
                ),
                rx.button(
                    rx.cond(
                        State.show_password,
                        "🙈",
                        "👁"
                    ),
                    on_click=State.toggle_show_password,
                    variant="ghost",
                    size="2",
                    ml="2"
                ),
                width="100%",
                align="center"
            ),
            
            # Confirmar Contraseña (Condicional)
            rx.cond(
                show_confirm,
                rx.input(
                    placeholder="Confirmar contraseña", 
                    type="password", 
                    value=State.confirmar_contraseña, 
                    on_change=State.set_confirmar_contraseña, 
                    bg="white",
                    color="black",
                    border="1px solid #718096",
                    _placeholder={"color": "#718096"},
                    width="100%", 
                    border_radius="md"
                )
            ),
            # Aviso inmediato si las contraseñas no coinciden
            rx.cond(
                show_confirm & (State.contraseña != State.confirmar_contraseña) & ((State.contraseña != "") | (State.confirmar_contraseña != "")),
                rx.text("Las contraseñas no coinciden.", color="red.500", font_size="sm", font_weight="bold")
            ),
            
            # Mensajes de estado con colores legibles
            rx.text(State.error_de_registro, color="red.500", font_size="sm", font_weight="bold"),
            rx.text(State.succes, color="green.500", font_size="sm", font_weight="bold"),
            
            rx.button(
                title, 
                on_click=on_submit, 
                width="100%", 
                color_scheme="blue", 
                size="4",
                margin_top="1em"
            ),
            spacing="4",
            align_items="center",
        ),
        width="100%",
        max_width="450px",
        padding="40px",
        box_shadow="0px 10px 25px rgba(0,0,0,0.2)",
        border_radius="xl",
        # Fondo de la tarjeta adaptativo para el Sprint 2
        bg="#f5f5f5"
    )


def navbar() -> rx.Component:
    # Barra de navegación principal con utility bar encima
    return rx.vstack(
        utility_bar(),
        rx.hstack(
            rx.link("Inicio", href="/", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}),
            rx.link("Nueva Solicitud", href="/solicitudes", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}),
            rx.link("Registro de Ciudadano", href="/registro", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}),
            rx.cond(State.es_autentica, rx.link("Cambiar Contraseña", href="/cambiar-contrasena", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}), rx.text("")),
            rx.link("Iniciar Sesión", href="/login", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}),
            spacing="6",
            padding="12px",
            width="100%",
            justify="center",
            bg="blue.600",
            box_shadow="md",
            position="sticky",
            top="0",
            z_index="sticky"
        )
    )


def utility_bar() -> rx.Component:
    """Barra superior delgada con logo GOV.CO, accesibilidad y enlaces de sesión."""
    return rx.hstack(
        rx.image(src="/assets/govco_logo.svg", alt="GOV.CO", height="28px"),
        rx.spacer(),
        rx.hstack(
            rx.link("Opciones de Accesibilidad", href="#", font_size="sm", color="gray.700"),
            rx.text("|"),
            rx.link("Inicia sesión", href="/login", font_size="sm", color="gray.700"),
            rx.text(" "),
            rx.link("Regístrate", href="/registro", font_size="sm", color="gray.700"),
            spacing="3",
            align_items="center"
        ),
        padding_x="16px",
        padding_y="6px",
        bg="#ffffff",
        border_bottom="1px solid #e6eef8",
        width="100%",
        align_items="center"
    )


def index() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        navbar(), # Agregamos el menú
        # Hero principal usando imagen de assets (fall back a estilo CSS con overlay)
        rx.box(
            rx.vstack(
                rx.heading("Atención PQRS - Enlace 1755", size="7", color="white"),
                rx.text("Atención PQRS - Enlace 1755", color="white", font_size="sm"),
                spacing="2",
                align_items="flex-start"
            ),
            width="100%",
            min_height="600px",
            style={
                "backgroundImage": "linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.35)), url('/assets/Gemini_Generated_Image_ouyornouyornouyo.png')",
                "backgroundSize": "cover",
                "backgroundPosition": "center",
                "backgroundRepeat": "no-repeat",
                "paddingLeft": "2rem",
                "paddingRight": "2rem",
                "paddingTop": "3rem",
                "paddingBottom": "3rem",
                "color": "white"
            },
            text_align="left"
        ),

        # Contenedor principal del landing con espacio y texto explicativo
        rx.center(
            rx.vstack(
                rx.container(
                    rx.vstack(
                        rx.heading("La Universidad del Valle te da la bienvenida al portal de gestión Enlace 1755", size="5", color="black"),
                        rx.text(
                            "Para nosotros es fundamental brindarte una atención transparente, oportuna y adecuada. Antes de registrar tu solicitud, por favor ten en cuenta los siguientes conceptos para clasificarla correctamente:",
                            color="gray.700",
                            font_size="md",
                            text_align="left"
                        ),
                        # Lista de definiciones
                        rx.vstack(
                            rx.hstack(rx.text("Petición:", font_weight="bold"), rx.text("Es el derecho de solicitar información, documentos o consultar sobre las actuaciones de la entidad.")),
                            rx.hstack(rx.text("Queja:", font_weight="bold"), rx.text("Manifestación de inconformidad frente a la conducta o actuar irregular de un funcionario.")),
                            rx.hstack(rx.text("Reclamo:", font_weight="bold"), rx.text("Manifestación por prestación deficiente de un servicio o incumplimiento de una obligación.")),
                            rx.hstack(rx.text("Sugerencia:", font_weight="bold"), rx.text("Recomendación o idea para mejorar servicios, procesos o atención de la institución.")),
                            spacing="3",
                            align_items="flex-start"
                        ),
                        spacing="6",
                        align_items="stretch"
                    ),
                    max_width="900px",
                    padding="6",
                    bg="white",
                    border_radius="md",
                    box_shadow="sm"
                ),

                # Botones de acción principales
                rx.hstack(
                    rx.link(rx.button("Radicar PQRS", color_scheme="blue", size="4", width="220px"), href="/solicitudes"),
                        rx.link(rx.button("Consultar Solicitud", color_scheme="gray", size="4", width="220px"), href="/consultar-estado"),
                    spacing="5",
                    align_items="center",
                    justify="center"
                ),

                spacing="8",
                align_items="center"
            ),
            min_height="64vh",
            width="100%",
            padding_top="10",
            padding_bottom="10",
            background="transparent"
        ),

        footer(),
        brand_footer()
    )


def footer() -> rx.Component:
    return rx.container(
        rx.hstack(
            # Columna 1: Información de la Entidad
            rx.vstack(
                rx.heading("Información de la Entidad", size="6", color="black"),
                rx.text("Sede Principal: Calle 10 # 5-20, Cali, Valle del Cauca"),
                rx.text("Código Postal: 760001"),
                rx.text("PBX: (+57) 602 XXX XXXX"),
                rx.link("Correo institucional: atencionalciudadano@empresa.gov.co", href="mailto:atencionalciudadano@empresa.gov.co"),
                rx.link("Sitio web principal: www.empresa.gov.co", href="http://www.empresa.gov.co", target="_blank"),
                rx.text("Horario de atención presencial: Lunes a Viernes, 7:30 a.m. - 12:00 p.m. y 2:00 p.m. - 5:30 p.m.")
            ),

            # Columna 2: Servicio al Ciudadano
            rx.vstack(
                rx.heading("Servicio al Ciudadano", size="6", color="black"),
                rx.link("Radicar solicitud PQRS (HU4)", href="/solicitudes"),
                rx.link("Consultar estado de solicitud (HU11)", href="/consultar-estado"),
                rx.link("Preguntas Frecuentes (FAQ)", href="/faq"),
                rx.link("Tiempos de respuesta (Ley 1755 de 2015)", href="/tiempos-respuesta"),
                rx.link("Notificaciones por aviso y judiciales", href="/notificaciones"),
                rx.link("Política de privacidad y protección de datos", href="/politica-privacidad"),
                rx.link("Manual de usuario (Enlace 1755)", href="/manual-1755")
            ),

            # Columna 3: Contacto Directo y Redes
            rx.vstack(
                rx.heading("Contacto Directo y Redes", size="6", color="black"),
                rx.text("Recepción de correspondencia física: Lunes a viernes, 8:00 a.m. a 4:00 p.m."),
                rx.text("Línea gratuita nacional: 01 8000 91XXXX"),
                rx.hstack(
                    rx.link("Facebook", href="https://facebook.com", target="_blank"),
                    rx.link("X/Twitter", href="https://twitter.com", target="_blank"),
                    rx.link("YouTube", href="https://youtube.com", target="_blank"),
                    rx.link("LinkedIn", href="https://linkedin.com", target="_blank"),
                    spacing="4"
                ),
                rx.text("Sistema gestionado por: Enlace 1755 (Versión 1.0)", font_size="sm")
            ),

            spacing="9",
            align_items="flex-start"
        ),
        width="100%",
        padding_top="24px",
        padding_bottom="24px",
        bg="#f7fafc",
        border_top="1px solid #e2e8f0",
        justify="center"
    )


def brand_footer() -> rx.Component:
    """Franja inferior con logos institucionales (Universidad del Valle y GOV.CO)."""
    return rx.container(
        rx.hstack(
            rx.image(src="/assets/unival_logo.svg", alt="Universidad del Valle", height="48px"),
            rx.spacer(),
            rx.image(src="/assets/govco_logo.svg", alt="Gobierno de Colombia", height="48px"),
            spacing="6",
            align_items="center",
            justify="center"
        ),
        width="100%",
        padding_top="12px",
        padding_bottom="12px",
        bg="#ffffff",
        border_top="1px solid #e2e8f0"
    )

def registro_page() -> rx.Component:
    return rx.container(
        navbar(),
        rx.center(
            # Llamamos a auth_card con la función de signup y pidiendo confirmación
            auth_card("Registrarme como Ciudadano", State.signup, show_confirm=True),
            min_height="8vh"
        )
    )


def change_password_page() -> rx.Component:
    return rx.container(
        navbar(),
        rx.center(
            rx.card(
                rx.vstack(
                    rx.heading("Cambiar Contraseña", size="7", color="black"),
                    rx.input(placeholder="Contraseña actual", type="password", value=State.current_password, on_change=State.set_current_password, width="100%"),
                    rx.input(placeholder="Nueva contraseña", type="password", value=State.new_password, on_change=State.set_new_password, width="100%"),
                    rx.input(placeholder="Confirmar nueva contraseña", type="password", value=State.confirm_new_password, on_change=State.set_confirm_new_password, width="100%"),
                    rx.button("Cambiar contraseña", on_click=State.change_password, color_scheme="blue", width="100%"),
                    rx.text(State.change_pw_message, color="green.500", font_size="sm")
                ),
                p="8",
                max_width="560px"
            ),
            min_height="84vh"
        )
    )

def login_page() -> rx.Component:
    return rx.container(
        navbar(),
        rx.center(
            rx.vstack(
                # Llamamos a auth_card. Nota: en tu código llamaste 'usuario' a la función de login
                auth_card("Iniciar Sesión", State.login,  show_confirm=False),
                # Enlace para ir a cambiar contraseña (visible siempre debajo del login)
                rx.link("¿Olvidaste tu contraseña?", href="/cambiar-contrasena", color_scheme="blue"),
                spacing="4",
                align_items="center"
            ),
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


def solicitudes_page() -> rx.Component:
    return rx.cond(
        State.es_autentica,
        rx.container(
            navbar(),
            rx.center(
                rx.card(
                    rx.vstack(
                        rx.heading("Nueva Solicitud PQRS", size="8", color="black"),
                        rx.text("Completa el formulario para radicar tu Petición, Queja, Reclamo o Sugerencia.", color="gray.600"),
                        rx.form(
                            rx.vstack(
                                rx.select(
                                    ["Petición", "Queja", "Reclamo", "Sugerencia"],
                                    placeholder="Selecciona el tipo de solicitud",
                                    value=State.tipo_solicitud,
                                    on_change=State.set_tipo_solicitud,
                                    required=True
                                ),
                                rx.input(
                                    placeholder="Asunto",
                                    value=State.asunto,
                                    on_change=State.set_asunto,
                                    required=True
                                ),
                                rx.text_area(
                                    placeholder="Descripción detallada",
                                    value=State.descripcion,
                                    on_change=State.set_descripcion,
                                    required=True,
                                    rows="4"
                                ),
                                rx.input(
                                    placeholder="Ubicación (opcional)",
                                    value=State.ubicacion,
                                    on_change=State.set_ubicacion
                                ),
                                # Archivo adjunto: se usa un input de tipo file para seleccionar desde el equipo
                                rx.input(
                                    placeholder="Documento adjunto (opcional)",
                                    type="file",
                                    on_change=State.set_documento,
                                    accept="*/*"
                                ),
                                rx.button("Enviar Solicitud", on_click=State.crear_solicitud, color_scheme="blue", width="100%"),
                                rx.cond(
                                    State.solicitud_mensaje,
                                    rx.text(State.solicitud_mensaje, color=rx.cond(State.solicitud_mensaje.contains("éxito"), "green.500", "red.500"))
                                ),
                                spacing="4",
                                align_items="stretch"
                            ),
                            on_submit=State.crear_solicitud
                        ),
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
                    rx.text("Necesitas iniciar sesión para crear una solicitud."),
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
app.add_page(solicitudes_page, route="/solicitudes", title="Nueva Solicitud PQRS")
app.add_page(change_password_page, route="/cambiar-contrasena", title="Cambiar Contraseña")
app.add_page(dashboard, route="/dashboard", title="Panel de Ciudadano")
