"""Sistema de Gestión de PQRS para Empresas Públicas - Sprint 1: Registro de Ciudadanos"""
import re
import datetime
from datetime import datetime
import bcrypt
import base64
import uuid
import os
import reflex as rx
from .usuario_model import Usuario, Solicitud
from sqlmodel import select, SQLModel, create_engine
from rxconfig import config
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from starlette.staticfiles import StaticFiles
from dotenv import load_dotenv
# Carpeta donde se guardarán los archivos subidos por los usuarios
UPLOAD_DIR = os.path.join(os.getcwd(), "assets", "uploads")
from typing import List, Dict, Any

# Cargar variables de entorno
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///reflex.db")
engine = create_engine(DATABASE_URL, echo=False)
SQLModel.metadata.create_all(engine)

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
    # Campos adicionales para registro extendido
    tipo_identificacion: str = ""
    numero_identificacion: str = ""
    nombres: str = ""
    apellidos: str = ""
    genero: str = ""
    direccion: str = ""
    telefono: str = ""
    departamento: str = ""
    ciudad: str = ""
    # Estados de validación UX
    correo_validado: bool = False
    numero_identificacion_valid: bool = False
    nombres_valid: bool = False
    apellidos_valid: bool = False
    telefono_valid: bool = False
    departamento_valid: bool = False
    ciudad_valid: bool = False
    # Habeas data / autorizaciones
    acepta_notificaciones: bool = False
    acepta_politica_datos: bool = False
    # Para el formulario de solicitudes
    acepta_politica_solicitud: bool = False
    tipo_solicitud: str = ""
    asunto: str = ""
    descripcion: str = ""
    ubicacion: str = ""
    documento: str = ""
    documento_nombre: str = ""
    descripcion_len: int = 0
    query_solicitud: str = ""
    filter_tipo_solicitud: str = "Todas"
    filter_estado_solicitud: str = "Todas"
    solicitudes: List[Dict] = []
    editar_solicitud_id: int = 0
    eliminar_solicitud_id: int = 0
    solicitud_mensaje: str = ""
    
    error_de_registro: str = ""
    succes: str = ""
    error_de_contraseña: str = ""
    succes2: str = ""
    
    id_usuario: int = 0
    es_autentica: bool = False
    email_actual: str = ""
    rol_usuario: str = ""
    email_actual: str = ""
    show_password: bool = False
    # Campos para cambiar contraseña
    current_password: str = ""
    new_password: str = ""
    confirm_new_password: str = ""
    change_pw_message: str = ""
    
    # Campos para búsqueda y filtros en dashboard funcionario
    busqueda_solicitudes: str = ""
    filtro_estado: str = ""
    filtro_tipo_solicitud: str = ""
    
    @rx.var
    def numero_solicitudes(self) -> str:
        return str(len(self.solicitudes or []))
    
    @rx.var
    def numero_solicitudes_radicadas(self) -> str:
        return str(sum(1 for solicitud in (self.solicitudes or []) if solicitud.get('estado') == 'Radicada'))
    
    @rx.var
    def numero_solicitudes_actualizadas(self) -> str:
        return str(sum(1 for solicitud in (self.solicitudes or []) if solicitud.get('estado') == 'Actualizada'))
    
    @rx.var
    def numero_solicitudes_cerradas(self) -> str:
        return str(sum(1 for solicitud in (self.solicitudes or []) if solicitud.get('estado') == 'Cerrada'))
    
    @rx.var
    def solicitudes_filtradas(self) -> list[dict]:
        query = (self.query_solicitud or "").strip().lower()
        tipo = (self.filter_tipo_solicitud or "Todas").lower()
        estado = (self.filter_estado_solicitud or "Todas").lower()
        resultados = []
        for solicitud in self.solicitudes or []:
            texto = " ".join(
                str(solicitud.get(field, "") or "")
                for field in ("radicado", "asunto", "descripcion", "creado_por")
            ).lower()
            if query and query not in texto:
                continue
            if tipo != "todas" and solicitud.get("tipo_solicitud", "").lower() != tipo:
                continue
            if estado != "todas" and solicitud.get("estado", "").lower() != estado:
                continue
            resultados.append(solicitud)
        return resultados
    
    def set_query_solicitud(self, value: str):
        self.query_solicitud = value or ""
    
    def set_filter_tipo_solicitud(self, value: str):
        self.filter_tipo_solicitud = value or "Todas"
    
    def set_filter_estado_solicitud(self, value: str):
        self.filter_estado_solicitud = value or "Todas"
    
    def set_new_password(self, value: str):
        self.new_password = value
    
    def set_confirm_new_password(self, value: str):
        self.confirm_new_password = value
    
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
    def validar_campo_simple(self, campo: str) -> bool:
        """Validaciones simples para mostrar iconos de confirmación.
        Retorna True si el campo parece correcto."""
        val = getattr(self, campo, "")
        ok = False
        if campo == "telefono":
            ok = isinstance(val, str) and len(val) >= 7
        elif campo == "numero_identificacion":
            ok = isinstance(val, str) and len(val) >= 6
        elif campo == "correo":
            ok = validar_correo(val)
        else:
            ok = bool(val and str(val).strip())
        # set dedicated flags for reactivity
        if campo == "telefono":
            self.telefono_valid = ok
        elif campo == "numero_identificacion":
            self.numero_identificacion_valid = ok
        elif campo == "nombres":
            self.nombres_valid = ok
        elif campo == "apellidos":
            self.apellidos_valid = ok
        elif campo == "departamento":
            self.departamento_valid = ok
        elif campo == "ciudad":
            self.ciudad_valid = ok
        return ok
        return ok

    def validar_correo_accion(self):
        """Acción invocada por el botón 'Validar' junto al correo."""
        self.correo_validado = validar_correo(self.correo)
        if not self.correo_validado:
            self.error_de_registro = "Correo inválido."
        else:
            self.error_de_registro = ""
        return

    # Setters that also validate so we can show inline icons
    def set_and_validate_nombres(self, val: str):
        self.nombres = val
        self.validar_campo_simple("nombres")

    def set_and_validate_apellidos(self, val: str):
        self.apellidos = val
        self.validar_campo_simple("apellidos")

    def set_and_validate_numero_identificacion(self, val: str):
        self.numero_identificacion = val
        self.validar_campo_simple("numero_identificacion")

    def set_and_validate_telefono(self, val: str):
        self.telefono = val
        self.validar_campo_simple("telefono")

    def set_and_validate_departamento(self, val: str):
        self.departamento = val
        self.validar_campo_simple("departamento")

    def set_and_validate_ciudad(self, val: str):
        self.ciudad = val
        self.validar_campo_simple("ciudad")

    def set_descripcion(self, val: str):
        # Guardar descripción y longitud para el contador de caracteres
        self.descripcion = val if val is not None else ""
        # Limitar a 1000 caracteres en la UI
        if len(self.descripcion) > 1000:
            self.descripcion = self.descripcion[:1000]
        self.descripcion_len = len(self.descripcion)

    def set_tipo_solicitud(self, val: str):
        self.tipo_solicitud = val or ""

    def set_asunto(self, val: str):
        self.asunto = val or ""

    def set_ubicacion(self, val: str):
        self.ubicacion = val or ""

    def set_acepta_politica_solicitud(self, checked: bool):
        self.acepta_politica_solicitud = bool(checked)

    def set_documento(self, documento: Any):
        """Actualiza el adjunto cuando el ciudadano selecciona un archivo."""
        if isinstance(documento, dict):
            name = documento.get("name") or documento.get("filename") or "adjunto"
            self.documento_nombre = name
            self.documento = documento
        elif isinstance(documento, str):
            self.documento_nombre = os.path.basename(documento)
            self.documento = documento
        else:
            self.documento_nombre = ""
            self.documento = documento

    def set_editar_solicitud_id(self, id: int):
        self.editar_solicitud_id = id

    def set_eliminar_solicitud_id(self, id: int):
        self.eliminar_solicitud_id = id

    def confirmar_editar_solicitud(self):
        if self.editar_solicitud_id:
            self.editar_solicitud(self.editar_solicitud_id)
            self.editar_solicitud_id = 0

    def confirmar_eliminar_solicitud(self):
        if self.eliminar_solicitud_id:
            self.eliminar_solicitud(self.eliminar_solicitud_id)
            self.eliminar_solicitud_id = 0

    def _solicitud_a_dict(self, solicitud: Solicitud) -> Dict[str, Any]:
        return {
            "id": solicitud.id,
            "radicado": solicitud.radicado,
            "tipo_solicitud": solicitud.tipo_solicitud,
            "asunto": solicitud.asunto,
            "descripcion": solicitud.descripcion,
            "ubicacion": solicitud.ubicacion,
            "documento": solicitud.documento,
            "documento_basename": solicitud.documento_basename,
            "estado": solicitud.estado,
            "fecha": solicitud.fecha.strftime("%Y-%m-%d %H:%M") if isinstance(solicitud.fecha, datetime) else str(solicitud.fecha),
            "creado_por": solicitud.creado_por,
            "usuario_id": solicitud.usuario_id,
        }

    def cargar_solicitudes(self):
        try:
            with rx.session() as session:
                query = select(Solicitud).order_by(Solicitud.id)
                if self.rol_usuario == "ciudadano" and self.email_actual:
                    query = query.where(Solicitud.creado_por == self.email_actual)
                solicitudes_obj = session.exec(query).all()
                self.solicitudes = [self._solicitud_a_dict(s) for s in solicitudes_obj]
        except Exception as e:
            print(f"Error cargando solicitudes: {e}")
            self.solicitudes = []

    def signup(self):
        self.borrar_mensajes_de_estado()
        if not self.validacion_de_entradas():
            return
        # Validaciones adicionales para registro extendido
        required_fields = ["nombres", "apellidos", "tipo_identificacion", "numero_identificacion"]
        for f in required_fields:
            if not getattr(self, f, ""):
                self.error_de_registro = "Completa los campos obligatorios de información personal."
                return
        if not self.acepta_politica_datos or not self.acepta_notificaciones:
            self.error_de_registro = "Debes aceptar la política de datos y recibir notificaciones para registrarte."
            return
        with rx.session() as session:
            existing_user = session.exec(select(Usuario).where(Usuario.email == self.correo)).first()
            if existing_user:
                self.error_de_registro = "El correo ya está registrado."
                return
            hashed = tiene_password(self.contraseña)
            nuevo_usuario = Usuario(
                email=self.correo,
                Contraseña=hashed,
                rol="ciudadano",
                is_active=True,
                Fecha_de_creacion=datetime.now(),
                tipo_identificacion=self.tipo_identificacion,
                numero_identificacion=self.numero_identificacion,
                nombres=self.nombres,
                apellidos=self.apellidos,
                genero=self.genero,
                direccion=self.direccion,
                telefono=self.telefono,
                departamento=self.departamento,
                ciudad=self.ciudad,
            )
            session.add(nuevo_usuario)
            session.commit()
            print(f"Usuario registrado: {self.correo}")
            # Enviar correo de bienvenida
            enviar_correo_bienvenida(self.correo, self.correo)
            self.succes = "Registro exitoso. Revisa tu correo para confirmar. Ahora el funcionario puede iniciar sesión."
            self.error_de_registro = ""
            self.contraseña = ""
            self.confirmar_contraseña = ""
            self.show_password = False

    def signup_funcionario(self):
        self.borrar_mensajes_de_estado()
        if not self.es_autentica or self.rol_usuario != "funcionario":
            self.error_de_registro = "Solo los funcionarios autenticados pueden registrar nuevos funcionarios."
            return
        if not self.validacion_de_entradas():
            return
        required_fields = ["nombres", "apellidos", "tipo_identificacion", "numero_identificacion"]
        for f in required_fields:
            if not getattr(self, f, ""):
                self.error_de_registro = "Completa los campos obligatorios de información personal."
                return
        if not self.acepta_politica_datos or not self.acepta_notificaciones:
            self.error_de_registro = "Debes aceptar la política de datos y recibir notificaciones para registrarte."
            return
        with rx.session() as session:
            existing_user = session.exec(select(Usuario).where(Usuario.email == self.correo)).first()
            if existing_user:
                self.error_de_registro = "El correo ya está registrado."
                return
            hashed = tiene_password(self.contraseña)
            nuevo_usuario = Usuario(
                email=self.correo,
                Contraseña=hashed,
                rol="funcionario",
                is_active=True,
                Fecha_de_creacion=datetime.now(),
                tipo_identificacion=self.tipo_identificacion,
                numero_identificacion=self.numero_identificacion,
                nombres=self.nombres,
                apellidos=self.apellidos,
                genero=self.genero,
                direccion=self.direccion,
                telefono=self.telefono,
                departamento=self.departamento,
                ciudad=self.ciudad,
            )
            session.add(nuevo_usuario)
            session.commit()
            print(f"Funcionario registrado: {self.correo}")
            enviar_correo_bienvenida(self.correo, self.correo)
            self.succes = "Funcionario registrado con éxito. Ahora puede iniciar sesión con su correo institucional."
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
            self.rol_usuario = user.rol
            self.email_actual = user.email
            self.es_autentica = True
            self.cargar_solicitudes()
            self.succes2 = f"Inicio de sesión exitoso. Redirigiendo al {'dashboard de funcionario' if user.rol == 'funcionario' else 'dashboard de ciudadano'}..."
            self.error_de_contraseña = ""
            self.contraseña = ""
            self.confirmar_contraseña = ""
            self.show_password = False
            if user.rol == "funcionario":
                return rx.redirect("/dashboard-funcionario")
            return rx.redirect("/dashboard")
    def logout(self):
        "cerrar sesion de usuario"
        self.id_usuario = 0
        self.correo = ""
        self.contraseña = ""
        self.confirmar_contraseña = ""
        self.rol_usuario = ""
        self.email_actual = ""
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

    def limpiar_formulario_solicitud(self, keep_message: bool = False):
        self.tipo_solicitud = ""
        self.asunto = ""
        self.descripcion = ""
        self.ubicacion = ""
        self.documento = ""
        self.documento_nombre = ""
        self.descripcion_len = 0
        self.editar_solicitud_id = 0
        self.acepta_politica_solicitud = False
        if not keep_message:
            self.solicitud_mensaje = ""

    def crear_solicitud(self):
        self.solicitud_mensaje = ""
        if not self.tipo_solicitud or not self.asunto or not self.descripcion:
            self.solicitud_mensaje = "Completa los campos obligatorios antes de enviar."
            return
        # Verificar aceptación de política de tratamiento de datos
        if not self.acepta_politica_solicitud:
            self.solicitud_mensaje = "Debes aceptar la Política de Tratamiento de Datos Personales antes de enviar."
            return

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

        if self.editar_solicitud_id:
            try:
                with rx.session() as session:
                    solicitud_obj = session.get(Solicitud, self.editar_solicitud_id)
                    if not solicitud_obj:
                        self.solicitud_mensaje = "Solicitud no encontrada para editar."
                        return
                    solicitud_obj.tipo_solicitud = self.tipo_solicitud
                    solicitud_obj.asunto = self.asunto
                    solicitud_obj.descripcion = self.descripcion
                    solicitud_obj.ubicacion = self.ubicacion or None
                    if documento_guardado:
                        solicitud_obj.documento = documento_guardado
                        solicitud_obj.documento_basename = os.path.basename(documento_guardado)
                    solicitud_obj.estado = "Actualizada"
                    session.add(solicitud_obj)
                    session.commit()
                self.solicitud_mensaje = "Solicitud actualizada con éxito."
                self.editar_solicitud_id = 0
                self.limpiar_formulario_solicitud(keep_message=True)
                self.cargar_solicitudes()
                return
            except Exception as e:
                self.solicitud_mensaje = f"Error actualizando solicitud: {e}"
                return

        try:
            with rx.session() as session:
                solicitud_obj = Solicitud(
                    radicado=f"PQRS-{datetime.now().year}-{uuid.uuid4().hex[:8]}",
                    tipo_solicitud=self.tipo_solicitud,
                    asunto=self.asunto,
                    descripcion=self.descripcion,
                    ubicacion=self.ubicacion or None,
                    documento=documento_guardado or None,
                    documento_basename=os.path.basename(documento_guardado) if documento_guardado else None,
                    estado="Radicada",
                    fecha=datetime.now(),
                    creado_por=self.email_actual or self.correo,
                    usuario_id=self.id_usuario if self.id_usuario else None,
                )
                session.add(solicitud_obj)
                session.commit()
            self.solicitud_mensaje = "Solicitud registrada correctamente."
            self.limpiar_formulario_solicitud(keep_message=True)
            self.cargar_solicitudes()
        except Exception as e:
            self.solicitud_mensaje = f"Error guardando solicitud: {e}"

    def signup_funcionario(self):
        self.borrar_mensajes_de_estado()
        if not self.validacion_de_entradas():
            return
        # Validaciones adicionales para registro de funcionario
        required_fields = ["nombres", "apellidos", "tipo_identificacion", "numero_identificacion"]
        for f in required_fields:
            if not getattr(self, f, ""):
                self.error_de_registro = "Completa los campos obligatorios de información personal."
                return
        if not self.acepta_politica_datos or not self.acepta_notificaciones:
            self.error_de_registro = "Debes aceptar la política de datos y recibir notificaciones para registrarte."
            return
        with rx.session() as session:
            existing_user = session.exec(select(Usuario).where(Usuario.email == self.correo)).first()
            if existing_user:
                self.error_de_registro = "El correo ya está registrado."
                return
            hashed = tiene_password(self.contraseña)
            nuevo_funcionario = Usuario(
                email=self.correo,
                Contraseña=hashed,
                rol="funcionario",
                is_active=True,
                Fecha_de_creacion=datetime.now(),
                tipo_identificacion=self.tipo_identificacion,
                numero_identificacion=self.numero_identificacion,
                nombres=self.nombres,
                apellidos=self.apellidos,
                genero=self.genero,
                direccion=self.direccion,
                telefono=self.telefono,
                departamento=self.departamento,
                ciudad=self.ciudad,
            )
            session.add(nuevo_funcionario)
            session.commit()
            print(f"Funcionario registrado: {self.correo}")
            enviar_correo_bienvenida(self.correo, self.correo)
            self.succes = "Funcionario registrado con éxito. Ahora puede iniciar sesión con su correo institucional."
            self.error_de_registro = ""
            self.contraseña = ""
            self.confirmar_contraseña = ""
            self.show_password = False

    def editar_solicitud(self, solicitud_id: int):
        try:
            with rx.session() as session:
                solicitud_obj = session.get(Solicitud, solicitud_id)
                if solicitud_obj:
                    self.editar_solicitud_id = solicitud_id
                    self.tipo_solicitud = solicitud_obj.tipo_solicitud
                    self.asunto = solicitud_obj.asunto
                    self.descripcion = solicitud_obj.descripcion
                    self.ubicacion = solicitud_obj.ubicacion or ""
                    self.documento = solicitud_obj.documento or ""
                    self.solicitud_mensaje = "Editando solicitud. Actualiza los campos y guarda cambios."
                else:
                    self.solicitud_mensaje = "Solicitud no encontrada."
        except Exception as e:
            self.solicitud_mensaje = f"Error cargando solicitud: {e}"

    def eliminar_solicitud(self, solicitud_id: int):
        try:
            with rx.session() as session:
                solicitud_obj = session.get(Solicitud, solicitud_id)
                if solicitud_obj:
                    session.delete(solicitud_obj)
                    session.commit()
                    self.solicitud_mensaje = "Solicitud eliminada correctamente."
                    self.cargar_solicitudes()
                else:
                    self.solicitud_mensaje = "Solicitud no encontrada."
        except Exception as e:
            self.solicitud_mensaje = f"Error eliminando solicitud: {e}"


    """The app state."""


def auth_card(title: str, on_submit, show_confirm: bool = False) -> rx.Component:
    # Si show_confirm es True, renderizamos el formulario extendido para registro
    if show_confirm:
        return rx.card(
            rx.form(
                rx.vstack(
                    rx.heading(title, size="7", color="black", margin_bottom="1em"),
                    # Grid de 2 columnas para campos personales
                    rx.grid(
                        # Responsive grid: 3 columnas en pantallas anchas
                        rx.vstack(rx.text("Tipo de Identificación", font_weight="semibold"), rx.select(["Cédula", "Pasaporte", "Tarjeta de Identidad"], placeholder="Selecciona", value=State.tipo_identificacion, on_change=State.set_tipo_identificacion, bg="white", border="1px solid #cbd5e1", border_radius="md")),
                        rx.vstack(rx.text([rx.text("Número de Identificación "), rx.text("*", color="orange.500")]), rx.hstack(rx.input(placeholder="Número de Identificación", value=State.numero_identificacion, on_change=State.set_and_validate_numero_identificacion, bg="white", border="1px solid #cbd5e1", border_radius="md"), rx.cond(State.numero_identificacion_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.vstack(rx.text([rx.text("Nombres "), rx.text("*", color="orange.500")]), rx.hstack(rx.input(placeholder="Nombres", value=State.nombres, on_change=State.set_and_validate_nombres, bg="white", border="1px solid #cbd5e1", border_radius="md"), rx.cond(State.nombres_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.vstack(rx.text([rx.text("Apellidos "), rx.text("*", color="orange.500")]), rx.hstack(rx.input(placeholder="Apellidos", value=State.apellidos, on_change=State.set_and_validate_apellidos, bg="white", border="1px solid #cbd5e1", border_radius="md"), rx.cond(State.apellidos_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.vstack(rx.text("Género"), rx.select(["Femenino", "Masculino", "Otro", "Prefiero no decirlo"], placeholder="Selecciona", value=State.genero, on_change=State.set_genero, bg="white", border="1px solid #cbd5e1", border_radius="md")),
                        rx.vstack(rx.text("Teléfono"), rx.hstack(rx.input(placeholder="Teléfono", value=State.telefono, on_change=State.set_and_validate_telefono, bg="white", border="1px solid #cbd5e1", border_radius="md"), rx.cond(State.telefono_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.vstack(rx.text("Departamento"), rx.hstack(rx.input(placeholder="Departamento", value=State.departamento, on_change=State.set_and_validate_departamento, bg="white", border="1px solid #cbd5e1", border_radius="md"), rx.cond(State.departamento_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.vstack(rx.text("Ciudad"), rx.hstack(rx.input(placeholder="Ciudad", value=State.ciudad, on_change=State.set_and_validate_ciudad, bg="white", border="1px solid #cbd5e1", border_radius="md"), rx.cond(State.ciudad_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.box(
                            rx.vstack(
                                rx.text([rx.text("Dirección "), rx.text("*", color="orange.500")]),
                                rx.input(
                                    placeholder="Dirección",
                                    value=State.direccion,
                                    on_change=State.set_direccion,
                                    bg="white",
                                    border="1px solid #cbd5e1",
                                    border_radius="md",
                                ),
                            ),
                            grid_column="1 / -1",
                        ),
                        rx.box(
                            rx.hstack(
                                rx.input(
                                    placeholder="Correo electrónico",
                                    type="email",
                                    value=State.correo,
                                    on_change=State.set_correo,
                                    bg="white",
                                    border="1px solid #cbd5e1",
                                    border_radius="md",
                                ),
                                rx.button("Validar", on_click=State.validar_correo_accion, color_scheme="blue", size="2", ml="2"),
                                rx.cond(State.correo_validado, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")),
                            ),
                            grid_column="1 / -1",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text([rx.text("Contraseña "), rx.text("*", color="orange.500")]),
                                rx.hstack(
                                    rx.cond(
                                        State.show_password,
                                        rx.input(
                                            placeholder="Contraseña",
                                            type="text",
                                            value=State.contraseña,
                                            on_change=State.set_contraseña,
                                            bg="white",
                                            border="1px solid #cbd5e1",
                                            border_radius="md",
                                        ),
                                        rx.input(
                                            placeholder="Contraseña",
                                            type="password",
                                            value=State.contraseña,
                                            on_change=State.set_contraseña,
                                            bg="white",
                                            border="1px solid #cbd5e1",
                                            border_radius="md",
                                        ),
                                    ),
                                    rx.button(
                                        rx.cond(State.show_password, "🙈", "👁"),
                                        on_click=State.toggle_show_password,
                                        variant="ghost",
                                        size="2",
                                        ml="2",
                                    ),
                                ),
                            ),
                            grid_column="1 / -1",
                        ),
                        rx.box(
                            rx.cond(
                                show_confirm,
                                rx.vstack(
                                    rx.text([rx.text("Confirmar Contraseña "), rx.text("*", color="orange.500")]),
                                    rx.input(
                                        placeholder="Confirmar Contraseña",
                                        type="password",
                                        value=State.confirmar_contraseña,
                                        on_change=State.set_confirmar_contraseña,
                                        bg="white",
                                        border="1px solid #cbd5e1",
                                        border_radius="md",
                                    ),
                                ),
                            ),
                            grid_column="1 / -1",
                        ),
                        template_columns="repeat(3, 1fr)",
                        gap="4",
                    ),

                    # Sección legal y checkboxes
                    rx.vstack(
                        rx.checkbox("Acepto recibir notificaciones por correo", is_checked=State.acepta_notificaciones, on_change=State.set_acepta_notificaciones),
                        rx.checkbox(rx.link("He leído y acepto la Política de Protección de Datos", href="/politica-privacidad", color="blue"), is_checked=State.acepta_politica_datos, on_change=State.set_acepta_politica_datos),
                        spacing="3",
                        padding_top="4"
                    ),

                    rx.text(State.error_de_registro, color="red.500", font_size="sm", font_weight="bold"),
                    rx.text(State.succes, color="green.500", font_size="sm", font_weight="bold"),

                    rx.hstack(rx.button(title, type="submit", color_scheme="blue", size="4", width="220px"), rx.link("¿No tienes una cuenta? Registrate", href="/login", margin_left="4"), spacing="4", justify="start"),

                    spacing="4",
                    align_items="stretch"
                ),
                on_submit=on_submit
            ),
            p="8",
            max_width="1100px",
            box_shadow="2xl",
            border_radius="2xl",
            bg="white",
            _dark={"bg": "gray.800"}
        )

    # Si no es registro extendido, renderizamos la forma simple (login)
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
            
            rx.link("¿No tienes cuenta? Regístrate", href="/registro", margin_top="0.5em"),
            spacing="4",
            align_items="center",
        ),
        p="8",
        max_width="450px",
        box_shadow="2xl",
        border_radius="2xl",
        bg="white",
        _dark={"bg": "gray.800"}
    )


def navbar() -> rx.Component:
    # Barra de navegación principal con utility bar encima
    return rx.vstack(
        utility_bar(),
        rx.hstack(
            rx.link("Inicio", href="/", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}),
            rx.link("Nueva Solicitud", href="/solicitudes", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}),
            rx.link("Registro de Ciudadano", href="/registro", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}),
            rx.cond(
                State.es_autentica & (State.rol_usuario == "funcionario"),
                rx.link("Registrar Funcionario", href="/registro-funcionario", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}),
                rx.text("")
            ),
            rx.cond(
                State.es_autentica & (State.rol_usuario == "funcionario"),
                rx.link("Dashboard Funcionario", href="/dashboard-funcionario", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}),
                rx.text("")
            ),
            rx.cond(
                State.es_autentica & (State.rol_usuario != "funcionario"),
                rx.link("Mi Dashboard", href="/dashboard", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}),
                rx.text("")
            ),
            rx.cond(State.es_autentica, rx.link("Cambiar Contraseña", href="/cambiar-contrasena", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"}), rx.text("")),
            rx.cond(
                State.es_autentica,
                rx.button("Cerrar Sesión", on_click=State.logout, color_scheme="red", size="4"),
                rx.link("Iniciar Sesión", href="/login", font_weight="bold", color_scheme="blue", text_decoration="none", _hover={"color":"gray.100"})
            ),
            spacing="6",
            padding="12px",
            width="100%",
            justify="center",
            bg="white",
            _dark={"bg": "gray.900", "borderColor": "gray.700"},
            box_shadow="md",
            border_bottom="1px solid #e6eef8",
            position="sticky",
            top="0",
            z_index="sticky"
        )
    )


def utility_bar() -> rx.Component:
    """Barra superior delgada con logo GOV.CO, accesibilidad y enlaces de sesión."""
    return rx.hstack(
        rx.image(src="/govco_logo.svg", alt="GOV.CO", height="28px"),
        rx.spacer(),
        rx.hstack(
            rx.link("Opciones de Accesibilidad", href="#", font_size="sm", color="white"),
            rx.text("|", color="white"),
            rx.link("Inicia sesión", href="/login", font_size="sm", color="white"),
            rx.text(" "),
            rx.link("Regístrate", href="/registro", font_size="sm", color="white"),
            spacing="3",
            align_items="center"
        ),
        padding_x="16px",
        padding_y="6px",
        bg="blue.600",
        border_bottom="1px solid rgba(0,0,0,0.08)",
        width="100%",
        align_items="center"
    )


def index() -> rx.Component:
    return rx.vstack(
        rx.color_mode.button(position="top-right"),

        # Header y banner de ancho completo
        rx.fragment(
            navbar(), # Barra superior (ya definida para 100% ancho)
            # Hero principal usando imagen de assets (full-width banner)
            rx.box(
                # inner centered container so text aligns with main content
                rx.container(
                    rx.vstack(
                        rx.heading("Atención PQRS - Enlace 1755", size="7", color="blue.600", style={"textShadow": "none"}),
                        rx.text("Atención PQRS - Enlace 1755", color="blue.600", font_size="sm", style={"textShadow": "none"}),
                        spacing="2",
                        align_items="flex-start"
                    ),
                    max_width="900px",
                    padding_x="6",
                    padding_y="2",
                    margin_x="auto"
                ),
                width="100%",
                min_height="220px",
                style={
                    "backgroundImage": "linear-gradient(rgba(0,0,0,0.15), rgba(0,0,0,0.15)), url('/Gemini_Generated_Image_ouyornouyornouyo.png')",
                    "backgroundSize": "cover",
                    "backgroundPosition": "center",
                    "backgroundRepeat": "no-repeat",
                    "color": "inherit"
                },
                text_align="left"
            )
        ),

        # Contenido principal centrado y con ancho limitado para legibilidad
        rx.container(
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
                                align_items="start"
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
            # container props: keep it visually centered but allow full-width header above
            padding_x="6"
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
                        align_items="start"
        ),
        width="100%",
        padding_top="24px",
        padding_bottom="24px",
        bg="#f7fafc",
        _dark={"bg": "gray.900", "borderColor": "gray.700"},
        border_top="1px solid #e2e8f0",
        justify="center"
    )


def brand_footer() -> rx.Component:
    """Franja inferior con logos institucionales (Universidad del Valle y GOV.CO)."""
    return rx.container(
        rx.hstack(
            rx.image(src="/unival_logo.svg", alt="Universidad del Valle", height="48px"),
            rx.spacer(),
            rx.image(src="/govco_logo.svg", alt="Gobierno de Colombia", height="48px"),
            spacing="6",
            align_items="center",
            justify="center"
        ),
        width="100%",
        padding_top="12px",
        padding_bottom="12px",
        bg="white",
        _dark={"bg": "gray.900", "borderColor": "gray.700"},
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


def registro_funcionario_page() -> rx.Component:
    return rx.cond(
        State.es_autentica & (State.rol_usuario == "funcionario"),
        rx.container(
            navbar(),
            rx.center(
                auth_card("Registrar Funcionario", State.signup_funcionario, show_confirm=True),
                min_height="8vh"
            )
        ),
        rx.container(
            navbar(),
            rx.center(
                rx.vstack(
                    rx.heading("Acceso Denegado", size="8", color="red.500"),
                    rx.text("Solo los funcionarios autenticados pueden registrar nuevos funcionarios."),
                    rx.link(rx.button("Ir al Login", color_scheme="blue"), href="/login"),
                    spacing="4",
                    align_items="center"
                ),
                min_height="84vh"
            )
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

def politica_privacidad_page() -> rx.Component:
    return rx.container(
        navbar(),
        rx.center(
            rx.box(
                rx.vstack(
                    rx.heading("Política de Privacidad y Protección de Datos", size="6", color="black"),
                    rx.text(
                        "En esta plataforma tratamos tus datos con responsabilidad, transparencia y seguridad. "
                        "Tu información personal se usa únicamente para gestionar solicitudes PQRS y mejorar el servicio.",
                        color="gray.700",
                        font_size="md"
                    ),
                    rx.text(
                        "Al enviar una solicitud aceptas la Política de Tratamiento de Datos Personales y los términos de uso de la plataforma.",
                        color="gray.700",
                        font_size="md"
                    ),
                    rx.heading("Datos recolectados", size="7", color="black"),
                    rx.text("Correo electrónico, identificación, nombre, apellidos, teléfono y datos de ubicación para poder gestionar la solicitud."),
                    rx.heading("Finalidad", size="7", color="black"),
                    rx.text("Usar tus datos para contactar al ciudadano, radicar la solicitud en el sistema y generar trazabilidad de atención."),
                    rx.heading("Derechos", size="7", color="black"),
                    rx.text("Puedes solicitar corrección o eliminación de tus datos conforme a la normativa vigente de protección de datos personales."),
                    rx.link("Volver al inicio", href="/", color_scheme="blue", font_weight="bold"),
                    spacing="4",
                    align_items="flex-start"
                ),
                p="8",
                max_width="840px",
                border_radius="2xl",
                bg="white",
                _dark={"bg": "gray.800"}
            ),
            min_height="84vh"
        )
    )

def dashboard() -> rx.Component:
    return rx.cond(
        State.es_autentica & (State.rol_usuario == "ciudadano"),
        rx.container(
            navbar(),
            rx.center(
                rx.vstack(
                    rx.heading("Panel de Ciudadano", size="8", color="black"),
                    rx.text("¡Bienvenido! Aquí podrás gestionar tus Peticiones, Quejas, Reclamos y Sugerencias.", color="gray.600"),
                    rx.box(
                        rx.vstack(
                            rx.heading("Mis Solicitudes", size="6", color="black"),
                            rx.cond(
                                State.solicitudes,
                                rx.vstack(
                                    rx.foreach(
                                        State.solicitudes,
                                        lambda solicitud: rx.box(
                                            rx.vstack(
                                                rx.heading(f"Radicado: {solicitud['radicado']} - {solicitud['tipo_solicitud']}", size="6", color="black"),
                                                rx.text(f"Asunto: {solicitud['asunto']}", color="gray.700"),
                                                rx.text(f"Descripción: {solicitud['descripcion']}", color="gray.700"),
                                                rx.text(f"Estado: {solicitud['estado']}", color="gray.600"),
                                                rx.text(f"Fecha: {solicitud['fecha']}", color="gray.600"),
                                                rx.cond(
                                                    solicitud["documento"],
                                                    rx.hstack(
                                                        rx.text("Documento: ", color="gray.600"),
                                                        rx.link(
                                                            solicitud["documento_basename"],
                                                            href=f"/assets/uploads/{solicitud['documento_basename']}",
                                                            color="blue.600",
                                                            target="_blank"
                                                        )
                                                    ),
                                                    rx.text("Documento: No adjunto", color="gray.600")
                                                ),
                                                spacing="2",
                                                align_items="start"
                                            ),
                                            p="4",
                                            border="1px solid #e2e8f0",
                                            border_radius="lg",
                                            bg="white",
                                            _dark={"bg": "gray.800", "borderColor": "gray.700"},
                                            width="100%"
                                        )
                                    ),
                                    spacing="4"
                                ),
                                rx.text("No tienes solicitudes registradas aún.", color="gray.600", font_size="md")
                            ),
                            spacing="4"
                        ),
                        width="100%"
                    ),
                    rx.button("Cerrar Sesión", on_click=State.logout, color_scheme="red", width="100%"),
                    spacing="6",
                    align_items="stretch"
                ),
                min_height="84vh"
            )
        ),
        rx.container(
            navbar(),
            rx.center(
                rx.vstack(
                    rx.heading("Acceso Denegado", size="8", color="red.500"),
                    rx.text("Esta página es solo para ciudadanos. Si eres funcionario, ve a tu dashboard.", color="gray.600"),
                    rx.link(rx.button("Ir al Dashboard Funcionario", color_scheme="blue"), href="/dashboard-funcionario"),
                    rx.link(rx.button("Ir al Login", color_scheme="gray"), href="/login"),
                    spacing="4",
                    align_items="center"
                ),
                min_height="84vh"
            )
        )
    )


def funcionario_dashboard() -> rx.Component:
    return rx.cond(
        State.es_autentica & (State.rol_usuario == "funcionario"),
        rx.container(
            navbar(),
            rx.center(
                rx.vstack(
                    rx.heading("Panel de Funcionario", size="8", color="black"),
                    rx.text("Bienvenido, funcionario. Esta es tu página principal donde puedes revisar todas las peticiones.", color="gray.600"),
                    rx.text("Usa el menú superior para navegar: 'Nueva Solicitud' para crear peticiones, 'Registrar Funcionario' para añadir nuevos funcionarios.", color="gray.500"),
                    rx.hstack(
                        rx.box(
                            rx.vstack(
                                rx.text("Total de solicitudes", font_weight="semibold", color="gray.600"),
                                rx.heading(State.numero_solicitudes, size="4", color="black")
                            ),
                            p="5",
                            border="1px solid #e2e8f0",
                            border_radius="xl",
                            bg="#f8fbff",
                            min_width="180px"
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("Radicadas", font_weight="semibold", color="gray.600"),
                                rx.heading(State.numero_solicitudes_radicadas, size="4", color="black")
                            ),
                            p="5",
                            border="1px solid #e2e8f0",
                            border_radius="xl",
                            bg="#fff7ed",
                            min_width="180px"
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("Actualizadas", font_weight="semibold", color="gray.600"),
                                rx.heading(State.numero_solicitudes_actualizadas, size="4", color="black")
                            ),
                            p="5",
                            border="1px solid #e2e8f0",
                            border_radius="xl",
                            bg="#f0fdf4",
                            min_width="180px"
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("Cerradas", font_weight="semibold", color="gray.600"),
                                rx.heading(State.numero_solicitudes_cerradas, size="4", color="black")
                            ),
                            p="5",
                            border="1px solid #e2e8f0",
                            border_radius="xl",
                            bg="#eef2ff",
                            min_width="180px"
                        ),
                        spacing="4",
                        width="100%",
                        flex_wrap="wrap"
                    ),
                    rx.box(
                        rx.vstack(
                            rx.cond(
                                State.solicitudes,
                                rx.vstack(
                                    rx.foreach(
                                        State.solicitudes,
                                        lambda solicitud: rx.box(
                                            rx.vstack(
                                                rx.heading(f"Radicado: {solicitud['radicado']} - {solicitud['tipo_solicitud']}", size="6", color="black"),
                                                rx.text(f"Asunto: {solicitud['asunto']}", color="gray.700"),
                                                rx.text(f"Descripción: {solicitud['descripcion']}", color="gray.700"),
                                                rx.text(f"Creado por: {solicitud.get('creado_por', 'Desconocido')}", color="gray.600"),
                                                rx.text(
                                                    "Ubicación: ",
                                                    rx.cond(
                                                        solicitud["ubicacion"],
                                                        solicitud["ubicacion"],
                                                        "No especificada"
                                                    ),
                                                    color="gray.600"
                                                ),
                                                rx.text(f"Estado: {solicitud['estado']}", color="gray.600"),
                                                rx.text(f"Fecha: {solicitud['fecha']}", color="gray.600"),
                                                rx.cond(
                                                    solicitud["documento"],
                                                    rx.hstack(
                                                        rx.text("Documento: ", color="gray.600"),
                                                        rx.link(
                                                            solicitud["documento_basename"],
                                                            href=f"/assets/uploads/{solicitud['documento_basename']}",
                                                            color="blue.600",
                                                            target="_blank"
                                                        )
                                                    ),
                                                    rx.text("Documento: No adjunto", color="gray.600")
                                                ),
                                                spacing="2",
                                                align_items="start"
                                            ),
                                            p="4",
                                            border="1px solid #e2e8f0",
                                            border_radius="lg",
                                            bg="white",
                                            _dark={"bg": "gray.800", "borderColor": "gray.700"},
                                            width="100%"
                                        )
                                    ),
                                    spacing="4"
                                ),
                                rx.text("No hay solicitudes registradas aún.", color="gray.600", font_size="md")
                            ),
                            spacing="4"
                        ),
                        width="100%"
                    ),
                    rx.button("Cerrar Sesión", on_click=State.logout, color_scheme="red", width="100%"),
                    spacing="6",
                    align_items="stretch"
                ),
                min_height="84vh"
            )
        ),
        rx.container(
            navbar(),
            rx.center(
                rx.vstack(
                    rx.heading("Acceso Denegado", size="8", color="red.500"),
                    rx.text("Solo los funcionarios autenticados pueden acceder a esta página."),
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
                                # Tipo de solicitud (label + select)
                                rx.vstack(
                                    rx.text([rx.text("Tipo de Solicitud ", font_weight="semibold"), rx.text("*", color="orange.500")], align_items="flex-start"),
                                    rx.select(["Petición", "Queja", "Reclamo", "Sugerencia"], placeholder="Selecciona el tipo de solicitud", value=State.tipo_solicitud, on_change=State.set_tipo_solicitud, required=True),
                                ),

                                # Asunto (label + input)
                                rx.vstack(
                                    rx.text([rx.text("Asunto ", font_weight="semibold"), rx.text("*", color="orange.500")]),
                                    rx.input(placeholder="Asunto", value=State.asunto, on_change=State.set_asunto, required=True, bg="white", border="1px solid #cbd5e1", border_radius="md"),
                                ),

                                # Descripción detallada (label + textarea + contador)
                                rx.vstack(
                                    rx.text([rx.text("Descripción detallada ", font_weight="semibold"), rx.text("*", color="orange.500")]),
                                    rx.text_area(placeholder="Escribe aquí los detalles de tu solicitud...", value=State.descripcion, on_change=State.set_descripcion, required=True, rows="4", max_length=1000, style={"resize": "vertical", "minHeight": "120px", "border": "1px solid #cbd5e1", "borderRadius": "8px", "padding": "8px"}, _dark={"bg": "gray.700", "color": "white", "borderColor": "gray.600"}),
                                    rx.hstack(rx.spacer(), rx.text(State.descripcion_len, font_size="sm", color="gray.600"), rx.text(" / 1000 caracteres", font_size="sm", color="gray.600")),
                                ),
                                rx.input(
                                    placeholder="Ubicación (opcional)",
                                    value=State.ubicacion,
                                    on_change=State.set_ubicacion
                                ),

                                # Archivo adjunto: zona arrastrar y soltar moderna
                                rx.vstack(
                                    rx.text("Documento adjunto (opcional)", font_weight="semibold"),
                                    rx.box(
                                        rx.hstack(
                                            rx.image(src="/clip-icon.svg", alt="Adjuntar", height="20px"),
                                            rx.text("Arrastra y suelta tus archivos aquí o haz clic para explorar", color="gray.600"),
                                            rx.spacer(),
                                            rx.text(State.documento_nombre, font_size="sm", color="gray.500")
                                        ),
                                        rx.input(type="file", accept="*/*", on_change=State.set_documento, style={"position": "absolute", "inset": "0", "width": "100%", "height": "100%", "opacity": 0, "cursor": "pointer"}),
                                        position="relative",
                                        padding="4",
                                        border="2px dashed #cfe7ff",
                                        border_radius="8px",
                                        bg="#f8fbff",
                                        _dark={"bg": "gray.700", "borderColor": "gray.600"},
                                        width="100%",
                                    )
                                ),
                                rx.checkbox(rx.link("He leído y acepto la Política de Tratamiento de Datos Personales", href="/politica-privacidad", color="blue"), is_checked=State.acepta_politica_solicitud, on_change=State.set_acepta_politica_solicitud),
                                rx.button("Enviar Solicitud", on_click=State.crear_solicitud, color_scheme="blue", width="100%", is_disabled=~State.acepta_politica_solicitud),
                                rx.cond(
                                    State.solicitud_mensaje,
                                    rx.text(State.solicitud_mensaje, color=rx.cond(State.solicitud_mensaje.contains("éxito"), "green.500", "red.500"))
                                ),
                                rx.cond(
                                    State.solicitudes,
                                    rx.vstack(
                                        rx.heading("Solicitudes registradas", size="6", color="black"),

                                        rx.foreach(
                                            State.solicitudes,
                                            lambda solicitud: rx.box(
                                                rx.vstack(
                                                    rx.text(f"#{solicitud['id']} - {solicitud['tipo_solicitud']}", font_weight="bold"),
                                                    rx.text(f"Asunto: {solicitud['asunto']}"),
                                                    rx.text(f"Descripción: {solicitud['descripcion']}"),
                                                    rx.text(f"Creado por: {solicitud.get('creado_por', 'Desconocido')}"),
                                                    rx.text(
                                                        "Ubicación: ",
                                                        rx.cond(
                                                            solicitud["ubicacion"],
                                                            solicitud["ubicacion"],
                                                            "No especificada"
                                                        )
                                                    ),
                                                    rx.text(f"Estado: {solicitud['estado']}"),
                                                    rx.text(f"Fecha: {solicitud['fecha']}"),
                                                    rx.cond(
                                                        solicitud["documento"],
                                                        rx.hstack(
                                                            rx.text("Documento: ", color="gray.600"),
                                                            rx.link(
                                                                solicitud["documento_basename"],
                                                                href=f"/assets/uploads/{solicitud['documento_basename']}",
                                                                color="blue.600",
                                                                target="_blank"
                                                            )
                                                        ),
                                                        rx.text("Documento: No adjunto", color="gray.600")
                                                    ),
                                                ),
                                                p="4",
                                                border="1px solid #e2e8f0",
                                                border_radius="lg",
                                                bg="white",
                                                _dark={"bg": "gray.800", "borderColor": "gray.700"},
                                                width="100%"
                                            )
                                        ),

                                        spacing="3",
                                        width="100%"
                                    )
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
app.add_page(registro_funcionario_page, route="/registro-funcionario", title="Registro de Funcionario")
app.add_page(login_page, route="/login", title="Iniciar Sesión")
app.add_page(solicitudes_page, route="/solicitudes", title="Nueva Solicitud PQRS")
app.add_page(change_password_page, route="/cambiar-contrasena", title="Cambiar Contraseña")
app.add_page(dashboard, route="/dashboard", title="Panel de Ciudadano")
app.add_page(funcionario_dashboard, route="/dashboard-funcionario", title="Panel de Funcionario")
app.add_page(politica_privacidad_page, route="/politica-privacidad", title="Política de Privacidad")
