from datetime import datetime
from flask import flash, redirect, session, url_for
import pytz
from functools import wraps
# Configurar la zona horaria para Asunción, Paraguay
asuncion_timezone = pytz.timezone('America/Asuncion')


def check_role(required_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Verificar si el usuario tiene la sesión y un rol asignado
            if 'rol' not in session:
                flash('Debes iniciar sesión para acceder a esta página.', 'danger')
                return redirect(url_for('login.index'))

            # Verificar si el rol del usuario está en la lista de roles requeridos
            """ if session['rol'] not in required_roles:
                flash('No tienes los privilegios suficientes para acceder a este módulo.', 'danger')
                return redirect(url_for('login.principal')) """
            
            if session['habilitation'] != 'A':
                flash('Su usuario se encuentra bloqueado.', 'danger')
                return redirect(url_for('login.index'))

            # Si todo está bien, ejecutar la función original
            return func(*args, **kwargs)

        return wrapper

    return decorator