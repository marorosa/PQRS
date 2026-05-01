"""Sistema de Gestión de PQRS para Empresas Públicas - Sprint 1: Registro de Ciudadanos"""
import re
from datetime import datetime
import bcrypt
import base64
import uuid
import os
import reflex as rx
from .usuario_model import Usuario, Solicitud
from sqlmodel import select, SQLModel, create_engine
from rxconfig import config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
    area_responsable: str = ""
    area_otro: str = ""
    tipo_solicitud: str = ""
    asunto: str = ""
    descripcion: str = ""
    ubicacion: str = ""
    documento: str = ""
    documento_nombre: str = ""
    descripcion_len: int = 0
    solicitudes: List[Dict] = []
    editar_solicitud_id: int = 0
    solicitud_mensaje: str = ""
    
    error_de_registro: str = ""
    succes: str = ""
    error_de_contraseña: str = ""
    succes2: str = ""
    
    id_usuario: int = 0
    es_autentica: bool = False
    email_actual: str = ""
    rol_usuario: str = ""
    show_password: bool = False
    # Campos para cambiar contraseña
    current_password: str = ""
    new_password: str = ""
    confirm_new_password: str = ""
    change_pw_message: str = ""
    # Campos para editar estado de solicitud
    editar_estado_id: int = 0
    nuevo_estado: str = ""
    respuesta_solicitud: str = ""
    mensaje_actualizar_estado: str = ""
    
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

    def set_documento(self, val):
        # Valida y guarda nombre/valor del documento enviado desde el input file
        # Valores posibles: dict con 'name' y 'content', o string (ruta/data URL)
        self.documento = val
        try:
            if isinstance(val, dict) and "name" in val:
                self.documento_nombre = val.get("name", "")
            elif isinstance(val, str):
                # puede ser data URL o ruta; mostrar solo la parte final
                self.documento_nombre = os.path.basename(val)
            else:
                self.documento_nombre = ""
        except Exception:
            self.documento_nombre = ""

    def set_area_responsable(self, val: str):
        self.area_responsable = val
        if val != "Otros":
            self.area_otro = ""

    def set_area_otro(self, val: str):
        self.area_otro = val

    def set_nuevo_estado(self, val: str):
        self.nuevo_estado = val

    def set_respuesta_solicitud(self, val: str):
        self.respuesta_solicitud = val

    def actualizar_estado_solicitud(self):
        """Actualiza el estado de una solicitud con validación para cerrada."""
        self.mensaje_actualizar_estado = ""
        
        if not self.editar_estado_id or not self.nuevo_estado:
            self.mensaje_actualizar_estado = "Selecciona un estado válido."
            return
        
        # Validar que si se quiere cerrar, debe haber respuesta
        if self.nuevo_estado == "Cerrada" and not self.respuesta_solicitud:
            self.mensaje_actualizar_estado = "No puedes cerrar una solicitud sin escribir una respuesta."
            return
        
        try:
            with rx.session() as session:
                solicitud_obj = session.get(Solicitud, self.editar_estado_id)
                if not solicitud_obj:
                    self.mensaje_actualizar_estado = "Solicitud no encontrada."
                    return
                
                solicitud_obj.estado = self.nuevo_estado
                if self.respuesta_solicitud:
                    solicitud_obj.respuesta = self.respuesta_solicitud
                
                session.add(solicitud_obj)
                session.commit()
            
            self.mensaje_actualizar_estado = f"Estado actualizado a '{self.nuevo_estado}' correctamente."
            self.editar_estado_id = 0
            self.nuevo_estado = ""
            self.respuesta_solicitud = ""
            self.cargar_solicitudes()
        except Exception as e:
            self.mensaje_actualizar_estado = f"Error actualizando estado: {e}"

    def abrir_editor_estado(self, solicitud_id: int, estado_actual: str):
        """Abre el editor de estado para una solicitud."""
        self.editar_estado_id = solicitud_id
        self.nuevo_estado = estado_actual
        self.respuesta_solicitud = ""
        self.mensaje_actualizar_estado = ""

    def _solicitud_a_dict(self, solicitud: Solicitud) -> Dict[str, Any]:
        return {
            "id": solicitud.id,
            "radicado": solicitud.radicado,
            "tipo_solicitud": solicitud.tipo_solicitud,
            "asunto": solicitud.asunto,
            "descripcion": solicitud.descripcion,
            "ubicacion": solicitud.ubicacion,
            "area_responsable": solicitud.area_responsable,
            "documento": solicitud.documento,
            "documento_basename": solicitud.documento_basename,
            "estado": solicitud.estado,
            "respuesta": solicitud.respuesta,
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

    def _validar_registro_basico(self) -> bool:
        if not self.validacion_de_entradas():
            return False
        required_fields = ["nombres", "apellidos", "tipo_identificacion", "numero_identificacion"]
        for f in required_fields:
            if not getattr(self, f, ""):
                self.error_de_registro = "Completa los campos obligatorios de información personal."
                return False
        if not self.acepta_politica_datos or not self.acepta_notificaciones:
            self.error_de_registro = "Debes aceptar la política de datos y recibir notificaciones para registrarte."
            return False
        return True

    def _crear_usuario(self, rol: str, exito_mensaje: str) -> bool:
        with rx.session() as session:
            existing_user = session.exec(select(Usuario).where(Usuario.email == self.correo)).first()
            if existing_user:
                self.error_de_registro = "El correo ya está registrado."
                return False
            hashed = tiene_password(self.contraseña)
            nuevo_usuario = Usuario(
                email=self.correo,
                Contraseña=hashed,
                rol=rol,
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
        enviar_correo_bienvenida(self.correo, self.correo)
        self.succes = exito_mensaje
        self.error_de_registro = ""
        self.contraseña = ""
        self.confirmar_contraseña = ""
        self.show_password = False
        return True

    def signup(self):
        self.borrar_mensajes_de_estado()
        if not self._validar_registro_basico():
            return
        self._crear_usuario(
            rol="ciudadano",
            exito_mensaje="Registro exitoso. Revisa tu correo para confirmar. Ahora el funcionario puede iniciar sesión.",
        )

    def signup_funcionario(self):
        self.borrar_mensajes_de_estado()
        if not self.es_autentica or self.rol_usuario != "funcionario":
            self.error_de_registro = "Solo los funcionarios autenticados pueden registrar nuevos funcionarios."
            return
        if not self._validar_registro_basico():
            return
        self._crear_usuario(
            rol="funcionario",
            exito_mensaje="Funcionario registrado con éxito. Ahora puede iniciar sesión con su correo institucional.",
        )

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
        self.area_responsable = ""
        self.area_otro = ""
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
        if not self.area_responsable:
            self.solicitud_mensaje = "Selecciona el área responsable."
            return
        if self.area_responsable == "Otros" and not self.area_otro:
            self.solicitud_mensaje = "Por favor indica el área responsable cuando eliges Otros."
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
                    solicitud_obj.area_responsable = self.area_otro if self.area_responsable == "Otros" else self.area_responsable
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
                    area_responsable=self.area_otro if self.area_responsable == "Otros" else self.area_responsable,
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
                    self.area_responsable = solicitud_obj.area_responsable or ""
                    self.area_otro = solicitud_obj.area_responsable if solicitud_obj.area_responsable and solicitud_obj.area_responsable not in ["Secretaría", "Contabilidad", "Bienestar", "Tesorería", "Atención al Ciudadano"] else ""
                    self.documento = solicitud_obj.documento or ""
                    self.solicitud_mensaje = "Editando solicitud. Actualiza los campos y guarda cambios."
                else:
                    self.solicitud_mensaje = "Solicitud no encontrada."
        except Exception as e:
            self.solicitud_mensaje = f"Error cargando solicitud: {e}"

    def eliminar_solicitud(self, solicitud_id: int):
        self.solicitudes = [s for s in self.solicitudes if s["id"] != solicitud_id]
        self.solicitud_mensaje = "Solicitud eliminada correctamente."

    """The app state."""


def auth_card(title: str, on_submit, show_confirm: bool = False) -> rx.Component:
    # Definición de colores que cambian según el tema
    text_color = rx.color_mode_cond(light="black", dark="white")
    input_bg = rx.color_mode_cond(light="white", dark="#2d3748") # gray.700 en modo oscuro
    input_border = rx.color_mode_cond(light="#cbd5e1", dark="#4a5568") # gray.600 en modo oscuro
    placeholder_color = rx.color_mode_cond(light="#718096", dark="#a0aec0")

    # Estilo base para los inputs
    input_style = {
        "bg": input_bg,
        "border": f"1px solid {input_border}",
        "color": text_color,
        "_placeholder": {"color": placeholder_color}
    }

    if show_confirm:
        return rx.card(
            rx.form(
                rx.vstack(
                    rx.heading(title, size="7", color=text_color, margin_bottom="1em"),
                    rx.grid(
                        rx.vstack(rx.text("Tipo de Identificación", font_weight="semibold", color=text_color), rx.select(["Cédula", "Pasaporte", "Tarjeta de Identidad"], placeholder="Selecciona", value=State.tipo_identificacion, on_change=State.set_tipo_identificacion, border_radius="md", **input_style)),
                        rx.vstack(rx.text([rx.text("Número de Identificación ", color=text_color), rx.text("*", color="orange.500")]), rx.hstack(rx.input(placeholder="Número de Identificación", value=State.numero_identificacion, on_change=State.set_and_validate_numero_identificacion, border_radius="md", **input_style), rx.cond(State.numero_identificacion_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.vstack(rx.text([rx.text("Nombres ", color=text_color), rx.text("*", color="orange.500")]), rx.hstack(rx.input(placeholder="Nombres", value=State.nombres, on_change=State.set_and_validate_nombres, border_radius="md", **input_style), rx.cond(State.nombres_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.vstack(rx.text([rx.text("Apellidos ", color=text_color), rx.text("*", color="orange.500")]), rx.hstack(rx.input(placeholder="Apellidos", value=State.apellidos, on_change=State.set_and_validate_apellidos, border_radius="md", **input_style), rx.cond(State.apellidos_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.vstack(rx.text("Género", color=text_color), rx.select(["Femenino", "Masculino", "Otro", "Prefiero no decirlo"], placeholder="Selecciona", value=State.genero, on_change=State.set_genero, border_radius="md", **input_style)),
                        rx.vstack(rx.text("Teléfono", color=text_color), rx.hstack(rx.input(placeholder="Teléfono", value=State.telefono, on_change=State.set_and_validate_telefono, border_radius="md", **input_style), rx.cond(State.telefono_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.vstack(rx.text("Departamento", color=text_color), rx.hstack(rx.input(placeholder="Departamento", value=State.departamento, on_change=State.set_and_validate_departamento, border_radius="md", **input_style), rx.cond(State.departamento_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.vstack(rx.text("Ciudad", color=text_color), rx.hstack(rx.input(placeholder="Ciudad", value=State.ciudad, on_change=State.set_and_validate_ciudad, border_radius="md", **input_style), rx.cond(State.ciudad_valid, rx.image(src="/check-green.svg", height="16px", ml="2"), rx.text("")))),
                        rx.box(
                            rx.vstack(
                                rx.text([rx.text("Dirección ", color=text_color), rx.text("*", color="orange.500")]),
                                rx.input(placeholder="Dirección", value=State.direccion, on_change=State.set_direccion, border_radius="md", **input_style),
                            ),
                            grid_column="1 / -1",
                        ),
                        template_columns="repeat(3, 1fr)",
                        gap="4",
                    ),
                    rx.vstack(
                        rx.checkbox("Acepto recibir notificaciones por correo", is_checked=State.acepta_notificaciones, on_change=State.set_acepta_notificaciones, color=text_color),
                        rx.checkbox(rx.link("He leído y acepto la Política de Protección de Datos", href="/politica-privacidad", color="blue.500"), is_checked=State.acepta_politica_datos, on_change=State.set_acepta_politica_datos, color=text_color),
                        spacing="3",
                        padding_top="4"
                    ),
                    rx.text(State.error_de_registro, color="red.500", font_size="sm", font_weight="bold"),
                    rx.text(State.succes, color="green.500", font_size="sm", font_weight="bold"),
                    rx.hstack(rx.button(title, type="submit", color_scheme="blue", size="4", width="220px"), rx.link("¿Ya tienes una cuenta? Inicia sesión", href="/login", margin_left="4", color="blue.500"), spacing="4", justify="start"),
                    spacing="4",
                    align_items="stretch"
                ),
                on_submit=on_submit
            ),
            p="8",
            max_width="1100px",
            box_shadow="2xl",
            border_radius="2xl",
            bg=rx.color_mode_cond(light="white", dark="#1a202c"), # Fondo de tarjeta adaptativo
        )


def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Agrupamos los links a la izquierda o centro
            rx.hstack(
                rx.link("Inicio", href="/", color="white", font_weight="bold", _hover={"opacity": 0.8}),
                rx.link("Nueva Solicitud", href="/solicitudes", color="white", font_weight="bold", _hover={"opacity": 0.8}),
                rx.link("Registro de Ciudadano", href="/registro", color="white", font_weight="bold", _hover={"opacity": 0.8}),
                rx.link("Dashboard", href="/dashboard", color="white", font_weight="bold", _hover={"opacity": 0.8}),
                spacing="6", # Espacio entre links
            ),
            # Botón de cerrar sesión a la derecha
            rx.button(
                "Cerrar Sesión", 
                on_click=State.logout, 
                color_scheme="red", 
                variant="solid"
            ),
            justify="between", # Separa los links del botón de cerrar sesión
            align_items="center",
            width="100%",
            max_width="1200px", # Limita el ancho en pantallas muy grandes
            margin="0 auto", # Centraliza el contenedor hstack
        ),
        bg="#1e40af", # El azul que vemos en image_6611fe.png
        padding_y="1em",
        padding_x="2em",
        width="100%",
    )

def utility_bar() -> rx.Component:
    return rx.hstack(
        rx.link("GOV.CO", href="/", font_weight="bold", color="white", text_decoration="none"),
        rx.spacer(),
        rx.hstack(
            rx.link("Opciones de Accesibilidad", href="#", font_size="sm", color="white", text_decoration="none"),
            rx.text("|", color="white"),
            rx.link("Inicia sesión", href="/login", font_size="sm", color="white", text_decoration="none"),
            rx.text("|", color="white"),
            rx.link("Regístrate", href="/registro", font_size="sm", color="white", text_decoration="none"),
            spacing="4",
            align_items="center"
        ),
        width="100%",
        padding_x="16px",
        padding_y="3",
        bg="#0f172a",
        border_bottom="1px solid rgba(255,255,255,0.08)"
    )


def index() -> rx.Component:
    hero_text = rx.color_mode_cond(light="rgba(15, 23, 42, 0.96)", dark="white")
    hero_sub = rx.color_mode_cond(light="rgba(15, 23, 42, 0.72)", dark="rgba(255,255,255,0.75)")
    card_bg = rx.color_mode_cond(light="white", dark="#111827")
    section_bg = rx.color_mode_cond(light="#f8fafc", dark="#020617")
    body_bg = rx.color_mode_cond(light="#f1f5f9", dark="#020617")

    return rx.box(
        rx.color_mode.button(position="top-right"),
        utility_bar(),
        navbar(),
        rx.box(
            rx.container(
                rx.hstack(
                    rx.vstack(
                        rx.text("Plataforma oficial de atención ciudadana", color="white", font_size="sm", bg="#2563eb", padding_x="3", padding_y="2", border_radius="full", mb="4"),
                        rx.heading("Atención PQRS - Enlace 1755", size="8", color="white", line_height="1.1"),
                        rx.text(
                            "Radica, consulta y gestiona tus Peticiones, Quejas, Reclamos y Sugerencias de forma clara, rápida y segura.",
                            color="rgba(255,255,255,0.85)",
                            font_size="lg",
                            max_width="680px"
                        ),
                        rx.hstack(
                            rx.link(rx.button("Radicar PQRS", color_scheme="blue", size="4", width="200px"), href="/solicitudes"),
                            rx.link(rx.button("Consultar estado", variant="outline", color_scheme="gray", size="4", width="200px"), href="/consultar-estado"),
                            spacing="4",
                            flex_wrap="wrap"
                        ),
                        spacing="6",
                        align_items="start",
                        width="100%",
                        max_width="720px"
                    ),
                    rx.card(
                        rx.vstack(
                            rx.heading("Accesos rápidos", size="5", color="#000000"),
                            rx.link(rx.button("Registrarme", color_scheme="blue", width="100%"), href="/registro"),
                            rx.link(rx.button("Iniciar sesión", variant="solid", color_scheme="gray", width="100%"), href="/login"),
                            rx.link(rx.button("Nueva solicitud", variant="outline", color_scheme="gray", width="100%"), href="/solicitudes"),
                            rx.text("Disponible para ciudadanos que deseen registrar y hacer seguimiento a sus solicitudes.", color="rgba(255,255,255,0.8)", font_size="sm"),
                            spacing="4",
                            align_items="stretch"
                        ),
                        p="6",
                        bg="rgba(255,255,255,0.08)",
                        border="1px solid rgba(255,255,255,0.15)",
                        border_radius="2xl",
                        width="100%",
                        max_width="340px"
                    ),
                    spacing="8",
                    align_items="center",
                    justify="between",
                    flex_wrap="wrap"
                ),
                max_width="1200px",
                padding_y="20",
                padding_x="6"
            ),
            width="100%",
            min_height="520px",
            style={
                "backgroundImage": "linear-gradient(90deg, rgba(15,23,42,0.84), rgba(15,23,42,0.30)), url('/Gemini_Generated_Image_ouyornouyornouyo.png')",
                "backgroundSize": "cover",
                "backgroundPosition": "center",
                "backgroundRepeat": "no-repeat"
            }
        ),

        rx.container(
            rx.vstack(
                rx.vstack(
                    rx.heading("¿Qué deseas hacer hoy?", size="7", color="#0f172a"),
                    rx.text("Accede rápidamente a los servicios principales del sistema.", color="#475569", font_size="md"),
                    spacing="3",
                    align_items="center"
                ),
                rx.hstack(
                    quick_action_card("Radicar PQRS", "Crea una nueva petición, queja, reclamo o sugerencia.", "Ir al formulario", "/solicitudes", "blue"),
                    quick_action_card("Consultar estado", "Revisa el avance y respuesta de tus solicitudes.", "Consultar", "/consultar-estado", "cyan"),
                    quick_action_card("Registro ciudadano", "Crea tu cuenta para gestionar trámites de forma segura.", "Registrarme", "/registro", "green"),
                    quick_action_card("Iniciar sesión", "Accede a tu cuenta y continúa tus gestiones.", "Entrar", "/login", "gray"),
                    spacing="5",
                    justify="center",
                    flex_wrap="wrap"
                ),
                spacing="9",
                align_items="center"
            ),
            max_width="1200px",
            padding_y="20",
            padding_x="6"
        ),

        rx.box(
            rx.container(
                rx.vstack(
                    rx.heading("Atención clara y transparente para la ciudadanía", size="7", color="#0f172a"),
                    rx.text("Este portal facilita la recepción, gestión y seguimiento de solicitudes ciudadanas de manera organizada y accesible.", color="#64748b", font_size="md", text_align="center", max_width="850px"),
                    spacing="4",
                    align_items="center"
                ),
                rx.hstack(
                    info_card("Canal seguro", "Tus datos y solicitudes se gestionan en un entorno controlado."),
                    info_card("Trazabilidad", "Cada solicitud puede registrarse y consultarse con mayor claridad."),
                    info_card("Atención oportuna", "El sistema está pensado para mejorar tiempos y experiencia ciudadana."),
                    spacing="5",
                    justify="center",
                    flex_wrap="wrap"
                ),
                spacing="9",
                align_items="center"
            ),
            width="100%",
            bg=section_bg,
            padding_y="20"
        ),

        rx.container(
            rx.vstack(
                rx.heading("¿Qué significa PQRS?", size="7", color="#0f172a"),
                rx.hstack(
                    pqrs_badge("Petición", "Solicitud respetuosa de información o actuación por parte de la entidad.", "#2563eb"),
                    pqrs_badge("Queja", "Manifestación de inconformidad por la conducta o atención recibida.", "#f59e0b"),
                    pqrs_badge("Reclamo", "Expresión de inconformidad por una prestación deficiente o incumplimiento.", "#ef4444"),
                    pqrs_badge("Sugerencia", "Propuesta o recomendación para mejorar la atención o el servicio.", "#10b981"),
                    spacing="5",
                    justify="center",
                    flex_wrap="wrap"
                ),
                spacing="8",
                align_items="center"
            ),
            max_width="1200px",
            padding_y="20",
            padding_x="6"
        ),

        footer(),
        brand_footer(),
        bg=body_bg,
        width="100%",
        min_height="100vh"
    )


def quick_action_card(title: str, desc: str, button_text: str, href: str, accent: str = "blue") -> rx.Component:
    card_bg = rx.color_mode_cond(light="white", dark="#111827")
    border = rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #334155")
    text_main = rx.color_mode_cond(light="#0f172a", dark="white")
    text_sec = rx.color_mode_cond(light="#475569", dark="#cbd5e1")

    return rx.card(
        rx.vstack(
            rx.heading(title, size="5", color=text_main),
            rx.text(desc, color=text_sec, font_size="sm"),
            rx.link(rx.button(button_text, color_scheme=accent, width="100%"), href=href),
            spacing="4",
            align_items="start",
            width="100%"
        ),
        bg=card_bg,
        border=border,
        border_radius="2xl",
        p="6",
        width="100%",
        max_width="260px",
        box_shadow="lg"
    )


def info_card(title: str, desc: str) -> rx.Component:
    card_bg = rx.color_mode_cond(light="white", dark="#111827")
    border = rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #334155")
    text_main = rx.color_mode_cond(light="#0f172a", dark="white")
    text_sec = rx.color_mode_cond(light="#475569", dark="#cbd5e1")

    return rx.card(
        rx.vstack(
            rx.text(title, font_weight="bold", color=text_main, font_size="md"),
            rx.text(desc, color=text_sec, font_size="sm"),
            spacing="3",
            align_items="start"
        ),
        bg=card_bg,
        border=border,
        border_radius="xl",
        p="5",
        width="100%",
        max_width="360px",
        box_shadow="sm"
    )


def pqrs_badge(title: str, desc: str, color: str) -> rx.Component:
    card_bg = rx.color_mode_cond(light="white", dark="#111827")
    border = rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #334155")
    text_sec = rx.color_mode_cond(light="#475569", dark="#cbd5e1")

    return rx.card(
        rx.vstack(
            rx.box(
                rx.text(title, color="white", font_weight="bold", font_size="sm"),
                bg=color,
                padding_x="3",
                padding_y="2",
                border_radius="full"
            ),
            rx.text(desc, color=text_sec, font_size="sm"),
            spacing="3",
            align_items="start"
        ),
        bg=card_bg,
        border=border,
        border_radius="xl",
        p="5",
        width="100%",
        max_width="360px",
        box_shadow="sm"
    )


def footer() -> rx.Component:
    header_color = rx.color_mode_cond(light="black", dark="white")
    text_color = rx.color_mode_cond(light="gray.700", dark="gray.400")
    link_color = rx.color_mode_cond(light="blue.600", dark="blue.300")
    bg_footer = rx.color_mode_cond(light="#f7fafc", dark="#111827")
    border_color = rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #2d3748")

    return rx.container(
        rx.hstack(
            # Columna 1: Información de la Entidad
            rx.vstack(
                rx.heading("Información de la Entidad", size="6", color=header_color),
                rx.text("Sede Principal: Calle 10 # 5-20, Cali, Valle del Cauca", color=text_color),
                rx.text("Código Postal: 760001", color=text_color),
                rx.text("PBX: (+57) 602 XXX XXXX", color=text_color),
                rx.link(
                    "Correo institucional: atencionalciudadano@empresa.gov.co", 
                    href="mailto:atencionalciudadano@empresa.gov.co",
                    color=link_color
                ),
                rx.link(
                    "Sitio web principal: www.empresa.gov.co", 
                    href="http://www.empresa.gov.co", 
                    target="_blank",
                    color=link_color
                ),
                rx.text(
                    "Horario de atención presencial: Lunes a Viernes, 7:30 a.m. - 12:00 p.m. y 2:00 p.m. - 5:30 p.m.",
                    color=text_color
                ),
                align_items="start",
            ),
            # Columna 2: Servicio al Ciudadano
            rx.vstack(
                rx.heading("Servicio al Ciudadano", size="6", color=header_color),
                rx.link("Radicar solicitud PQRS (HU4)", href="/solicitudes", color=link_color),
                rx.link("Consultar estado de solicitud (HU11)", href="/consultar-estado", color=link_color),
                rx.link("Preguntas Frecuentes (FAQ)", href="/faq", color=link_color),
                rx.link("Tiempos de respuesta (Ley 1755 de 2015)", href="/tiempos-respuesta", color=link_color),
                rx.link("Notificaciones por aviso y judiciales", href="/notificaciones", color=link_color),
                rx.link("Política de privacidad y protección de datos", href="/politica-privacidad", color=link_color),
                rx.link("Manual de usuario (Enlace 1755)", href="/manual-1755", color=link_color),
                align_items="start",
            ),
            # Columna 3: Contacto Directo y Redes
            rx.vstack(
                rx.heading("Contacto Directo y Redes", size="6", color=header_color),
                rx.text("Recepción de correspondencia física: Lunes a viernes, 8:00 a.m. a 4:00 p.m.", color=text_color),
                rx.text("Línea gratuita nacional: 01 8000 91XXXX", color=text_color),
                rx.hstack(
                    rx.link("Facebook", href="https://facebook.com", target="_blank", color=link_color),
                    rx.link("X/Twitter", href="https://twitter.com", target="_blank", color=link_color),
                    rx.link("YouTube", href="https://youtube.com", target="_blank", color=link_color),
                    rx.link("LinkedIn", href="https://linkedin.com", target="_blank", color=link_color),
                    spacing="4"
                ),
                rx.text("Sistema gestionado por: Enlace 1755 (Versión 1.0)", font_size="sm", color=text_color),
                align_items="start",
            ),
            spacing="9",
            align_items="start"
        ),
        width="100%",
        padding_top="24px",
        padding_bottom="24px",
        bg=bg_footer,
        border_top=border_color,
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
@rx.page(route="/login", title="Iniciar Sesión")
def login_page() -> rx.Component:
    return rx.vstack(
        navbar(),  # Tu barra de navegación superior
        rx.center(  # Este componente es clave para el centrado total
            rx.card(
                rx.vstack(
                    rx.heading("Iniciar Sesión", size="7", margin_bottom="1em"),
                    rx.input(
                        placeholder="Correo electrónico", 
                        on_change=State.set_correo,
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Contraseña", 
                        type_="password", 
                        on_change=State.set_contraseña,
                        width="100%",
                    ),
                    # Mensaje de éxito/error dinámico
                    rx.cond(
                        State.succes2 != "",
                        rx.text(State.succes2, color="green", font_size="0.9em"),
                    ),
                    rx.button(
                        "Entrar", 
                        on_click=State.login, 
                        color_scheme="blue", 
                        width="100%",
                        margin_top="1em"
                    ),
                    rx.link(
                        "¿No tienes cuenta? Regístrate", 
                        href="/registro", 
                        font_size="0.8em",
                        color="#60a5fa"
                    ),
                    spacing="4",
                    padding="1.5em",
                ),
                width="400px", # Ancho fijo para que se vea como una tarjeta
                box_shadow="lg",
                border_radius="15px",
            ),
            width="100%",
            # Calculamos el alto restando la altura aproximada de la navbar
            min_height="85vh", 
        ),
        bg=rx.color_mode_cond(light="#f4f4f5", dark="#0f172a"),
        width="100%",
        min_height="100vh",
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
                                                rx.text(
                                                    "Área responsable: ",
                                                    rx.cond(
                                                        solicitud["area_responsable"],
                                                        solicitud["area_responsable"],
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
                                                            href=f"/uploads/{solicitud['documento_basename']}",
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

                                rx.vstack(
                                    rx.text([rx.text("Área Responsable ", font_weight="semibold"), rx.text("*", color="orange.500")]),
                                    rx.select(
                                        ["Secretaría", "Contabilidad", "Bienestar", "Tesorería", "Atención al Ciudadano", "Otros"],
                                        placeholder="Selecciona el área responsable",
                                        value=State.area_responsable,
                                        on_change=State.set_area_responsable,
                                        required=True,
                                        bg="white",
                                        border="1px solid #cbd5e1",
                                        border_radius="md",
                                    ),
                                ),

                                rx.cond(
                                    State.area_responsable == "Otros",
                                    rx.vstack(
                                        rx.text([rx.text("Otra área", font_weight="semibold"), rx.text("*", color="orange.500")]),
                                        rx.input(
                                            placeholder="Escribe el área responsable",
                                            value=State.area_otro,
                                            on_change=State.set_area_otro,
                                            required=True,
                                            bg="white",
                                            border="1px solid #cbd5e1",
                                            border_radius="md",
                                        ),
                                    )
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
                                        bg="#263ba4",
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
                                                    rx.text(
                                                        "Área responsable: ",
                                                        rx.cond(
                                                            solicitud["area_responsable"],
                                                            solicitud["area_responsable"],
                                                            "No especificada"
                                                        )
                                                    ),
                                                    rx.text(f"Estado: {solicitud['estado']}"),
                                                    rx.text(f"Fecha: {solicitud['fecha']}"),
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
