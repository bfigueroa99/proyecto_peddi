from datetime import datetime
from models import Formulario, PersonaFormulario
from app import crear_multipropietario, agregar_multipropietario
from app import crear_persona_formulario, existe_persona_formulario
from app import obtener_porcentaje_total, crear_formulario
from app import obtener_cantidad_porcentajes_nulos
from app import agrupar_propietarios_repetidos

ESTADO_ACTUAL = "actual"
global multipropietarios
multipropietarios = []

def test_crear_multipropietario(session):
    multipropietario = crear_multipropietario(
        '12345678-9', 1, 40, 400,
        None, 50, 100, 1, 2021)
    assert multipropietario.rut == '12345678-9'
    assert multipropietario.comuna_id == 1
    assert multipropietario.porcentaje_der == 50

def test_crear_formulario(session):
    fecha_prueba = datetime(2023, 6, 1, 12, 0, 0)
    crear_formulario(1, 8, 1, 40, 400, 100, fecha_prueba, 1)
    formulario = session.query(Formulario).filter_by(num_atencion=1).first()
    assert formulario is not None
    assert formulario.cne == 8

def test_crear_persona_formulario(session):
    rut = "11111111-1"
    numero_atencion = "12"
    porcentaje_der = 40
    rol = "adquirente"
    crear_persona_formulario(rut, numero_atencion, porcentaje_der, rol)
    persona_formulario = session.query(PersonaFormulario).filter_by(
        rut=rut,
        num_atencion=numero_atencion,
        rol=rol).first()
    assert persona_formulario.rut == "11111111-1"
    assert persona_formulario.num_atencion == "12"
    assert persona_formulario.rol == "adquirente"

def test_existe_persona_formulario(session):
    persona_formulario = existe_persona_formulario("11111111-1",
                                                   "12",
                                                   "adquirente")
    assert persona_formulario is not None

def test_agregar_multipropietario(session):
    global multipropietarios

    formulario_actual = Formulario(
        num_atencion=1,
        cne=8,
        comuna_id=1,
        manzana=40,
        predio=400,
        fojas=100,
        fecha_ins=datetime.now(),
        num_ins=1
    )

    formulario_anterior = Formulario(
        num_atencion=2,
        cne=8,
        comuna_id=1,
        manzana=80,
        predio=800,
        fojas=150,
        fecha_ins=datetime(2022, 1, 1),
        num_ins=2
    )
    agregar_multipropietario('12345678-9',
                            50, formulario_actual, formulario_anterior,
                            multipropietarios, ESTADO_ACTUAL)

    agregar_multipropietario('12345678-9',
                            30, formulario_actual, formulario_anterior,
                            multipropietarios, ESTADO_ACTUAL)
    assert len(multipropietarios) == 2

def test_obtener_porcentaje_total(session):
    global multipropietarios
    porcentaje_total = obtener_porcentaje_total(multipropietarios)
    assert porcentaje_total == 80

def test_obtener_cantidad_porcentajes_nulos(session):
    global multipropietarios
    porcentaje_total = obtener_cantidad_porcentajes_nulos(multipropietarios)
    assert porcentaje_total == 0

def test_agrupar_propietarios_repetidos(session):
    global multipropietarios
    agrupar_propietarios_repetidos(multipropietarios)
    assert len(multipropietarios) == 1
