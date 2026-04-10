from datetime import datetime
from typing import Optional
import reflex as rx
from sqlmodel import Field

class Usuario(rx.Model, table=True):
    "Esta es la tabla de usuario en la base de datos"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    Contraseña: str
    rol: str = "ciudadano"  # Roles: ciudadano, funcionario, administrador
    is_active: bool = True
    Fecha_de_creacion: datetime = Field(default_factory=datetime.now)
    