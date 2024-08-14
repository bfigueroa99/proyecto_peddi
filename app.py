"""
Este es un módulo que contiene todas las funciones y rutas para que
la app funcione correctamente. Es decir, es el backend de la aplicación,
o la app en sí.
"""
from random import choices
from string import digits
from datetime import datetime
from json import loads
from json.decoder import JSONDecodeError
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask, render_template, request, jsonify, flash
from models import Base, Formulario, PersonaFormulario, Region
from models import Comuna, Multipropietario
from database import session, LLAVE

ESTADO_ANTERIOR = "anterior"
ESTADO_ACTUAL = "actual"
ESTADO_FANTASMA = "fantasma"
MINIMO_PORCENTAJE = 0
MAXIMO_PORCENTAJE = 100
CNE_COMPRAVENTA = 8
UNITARIO = 1
HOME_PAGE = "home.html"

# pylint: disable=R0913
def crear_multipropietario(
        rut, comuna_id, manzana, predio, fecha_inscripcion,
        porcentaje_derecho, fojas, numero_inscripcion,
        ano_vigencia_inicial):
    if fecha_inscripcion:
        ano_ins = fecha_inscripcion.year
    else:
        ano_ins = None
    multipropietario = Multipropietario(
        rut=rut,
        comuna_id=comuna_id,
        manzana=manzana,
        predio=predio,
        fecha_ins=fecha_inscripcion,
        porcentaje_der=porcentaje_derecho,
        fojas=fojas,
        ano_ins=ano_ins,
        num_ins=numero_inscripcion,
        ano_vigencia_inicial=ano_vigencia_inicial)
    return multipropietario


def crear_formulario(
        num_atencion, cne, comuna_id, manzana, predio,
        fojas, fecha_inscripcion, numero_inscripcion):
    formulario = Formulario(
        num_atencion=num_atencion,
        cne=cne,
        comuna_id=comuna_id,
        manzana=manzana,
        predio=predio,
        fojas=fojas,
        fecha_ins=fecha_inscripcion,
        num_ins=numero_inscripcion)
    session.add(formulario)
    session.commit()



def crear_persona_formulario(rut, numero_atencion, porcentaje_derecho, rol):
    """
    Función que actualiza el porcentaje de derecho de una persona
    existente o crea un nuevo registro de PersonaFormulario en la
    base de datos si no existe.
    """
    persona_formulario = session.query(PersonaFormulario).filter_by(
        rut=rut,
        num_atencion=numero_atencion,
        rol=rol
    ).first()
    if persona_formulario:
        persona_formulario.porcentaje_der += porcentaje_derecho
    else:
        persona_formulario = PersonaFormulario(
            rut=rut,
            num_atencion=numero_atencion,
            porcentaje_der=porcentaje_derecho,
            rol=rol
        )
        session.add(persona_formulario)
        session.commit()


def eliminar_multipropietario(formulario, multipropietarios, persona):
    """
    Permite heredar propietarios de la tabla Multipropietarios
    para formularios del mismo año, mediante su eliminación.
    """
    for multipropietario in multipropietarios:
        ano_inicial1 = multipropietario.get_ano_vigencia_inicial
        ano_inicial2 = formulario.get_fecha_ins.year
        rut1 = multipropietario.get_rut
        rut2 = persona.get_rut
        if ano_inicial1 == ano_inicial2 and rut1 == rut2:
            multipropietarios.remove(multipropietario)
            break
    return multipropietarios


def agregar_multipropietario(
        rut, porcentaje_derecho, formulario,
        formulario_anterior, multipropietarios, estado):
    """
    Función agrega un nuevo multipropietario a la lista con características
    basadas en el estado proporcionado (actual, anterior o fantasma).
    """
    if estado == ESTADO_ACTUAL:
        # Multipropietario con caracteristicas del formulario actual.
        fecha_inscripcion = formulario.get_fecha_ins
        fojas = formulario.get_fojas
        numero_inscripcion = formulario.get_num_ins
    elif estado == ESTADO_ANTERIOR:
        # Multipropietario con caracteristicas del formulario anterior.
        fecha_inscripcion = formulario_anterior.get_fecha_ins
        fojas = formulario_anterior.get_fojas
        numero_inscripcion = formulario_anterior.get_num_ins
    else:
        # Multipropietario fantasma.
        fecha_inscripcion = None
        fojas = None
        numero_inscripcion = None
    # Adición del multipropietario en cuestión a la lista.
    multipropietarios.append(crear_multipropietario(
        rut,
        formulario.get_comuna_id,
        formulario.get_manzana,
        formulario.get_predio,
        fecha_inscripcion,
        porcentaje_derecho,
        fojas,
        numero_inscripcion,
        formulario.get_fecha_ins.year))
    return multipropietarios


def agregar_escenario1_cne8(
        formulario, formulario_anterior, propietarios_no_enajenantes,
        enajenantes_no_fantasma, adquirentes, multipropietarios, mismo_ano,
        dominio_enajenantes):
    """
    Función que actualiza la lista de multipropietarios agregando
    propietarios no enajenantes, eliminando enajenantes no fantasma, y
    añadiendo adquirentes con porcentajes de derecho ajustados.
    """
    if not mismo_ano:
        multipropietarios = agregar_propietarios_no_enajenantes(
            formulario, formulario_anterior,
            multipropietarios, propietarios_no_enajenantes)
    else:
        for persona in enajenantes_no_fantasma:
            # Eliminación de adquirentes.
            multipropietarios = eliminar_multipropietario(
                formulario, multipropietarios, persona)
    for persona in adquirentes:
        # Adición de adquirentes.
        multipropietarios = agregar_multipropietario(
            persona.get_rut,
            (persona.get_porcentaje_der*dominio_enajenantes)/MAXIMO_PORCENTAJE,
            formulario,
            formulario_anterior,
            multipropietarios,
            ESTADO_ACTUAL)
    return multipropietarios


def agregar_escenario2_cne8(
        formulario, formulario_anterior,
        propietarios_no_enajenantes, enajenantes,
        adquirentes, multipropietarios, mismo_ano,
        dominio_enajenantes):
    """
    Función que actualiza la lista de multipropietarios agregando
    propietarios no enajenantes, eliminando enajenantes, y añadiendo
    adquirentes con porcentajes de derecho distribuidos equitativamente.
    """
    if not mismo_ano:
        multipropietarios = agregar_propietarios_no_enajenantes(
            formulario, formulario_anterior,
            multipropietarios, propietarios_no_enajenantes)
    else:
        for persona in enajenantes:
            # Eliminación de enajenantes.
            multipropietarios = eliminar_multipropietario(
                formulario, multipropietarios, persona)
    for persona in adquirentes:
        # Adición de adquirentes.
        multipropietarios = agregar_multipropietario(
            persona.get_rut,
            dominio_enajenantes/len(adquirentes),
            formulario,
            formulario_anterior,
            multipropietarios,
            ESTADO_ACTUAL)
    return multipropietarios

def ajustar_multipropietario(multipropietarios):
    """
    Función que ajusta los porcentajes de derecho de los multipropietarios
    para que el total cumpla con el máximo permitido, y devuelve una lista
    de multipropietarios con porcentajes positivos.
    """
    porcentaje_total = obtener_porcentaje_total(multipropietarios)
    cantidad_nulos = obtener_cantidad_porcentajes_nulos(multipropietarios)
    numerador_porcentaje = MAXIMO_PORCENTAJE - porcentaje_total

    for multipropietario in multipropietarios:
        ajustar_porcentaje(multipropietario, numerador_porcentaje, porcentaje_total, cantidad_nulos)

    return [mp for mp in multipropietarios if mp.get_porcentaje_der() > MINIMO_PORCENTAJE]

def ajustar_porcentaje(multipropietario, numerador_porcentaje,
                       porcentaje_total, cantidad_nulos):
    """
    Función auxiliar que ajusta el porcentaje de derecho de un multipropietario
    según las reglas establecidas.
    """
    ultimo_ano_inicial = multipropietario[-1].get_ano_vigencia_inicial()
    ano_inicial = multipropietario.get_ano_vigencia_inicial()
    porcentaje_der = multipropietario.get_porcentaje_der()

    if ultimo_ano_inicial == ano_inicial:
        if round(porcentaje_total, 5) < MAXIMO_PORCENTAJE and \
            porcentaje_der <= MINIMO_PORCENTAJE:
            reparto_porcentaje = numerador_porcentaje / cantidad_nulos
            multipropietario.porcentaje_der = reparto_porcentaje
        elif round(porcentaje_total, 5) > MAXIMO_PORCENTAJE:
            ponderador_porcentaje = MAXIMO_PORCENTAJE / porcentaje_total
            multipropietario.porcentaje_der *= ponderador_porcentaje


def agregar_propietarios_no_enajenantes(
        formulario, formulario_anterior,
        multipropietarios, propietarios_no_enajenantes):
    """
    Función que agrega propietarios no enajenantes a la lista
    multipropietarios, asignándo el estado según número de inscripción.
    """
    for persona in propietarios_no_enajenantes:
        if persona.get_num_ins:
            estado = ESTADO_ANTERIOR
        else:
            estado = ESTADO_FANTASMA
        # Adición de propietarios (no enajenantes).
        multipropietarios = agregar_multipropietario(
            persona.get_rut,
            persona.get_porcentaje_der,
            formulario,
            formulario_anterior,
            multipropietarios,
            estado)
    return multipropietarios

def reducir_porcentaje_enajenantes(multipropietarios, formulario,
                                   enajenantes_no_fantasma):
    """
    Función que reduce el porcentaje de derecho de un enajenante en la lista
    de multipropietarios según su porcentaje actual y el porcentaje del
    enajenante no fantasma correspondiente.
    """
    for multipropietario in multipropietarios:
        ano_inicial1 = multipropietario.get_ano_vigencia_inicial
        ano_inicial2 = formulario.get_fecha_ins.year
        rut1 = multipropietario.get_rut
        rut2 = enajenantes_no_fantasma[0].get_rut
        porcentaje_enajenante = enajenantes_no_fantasma[0].get_porcentaje_der
        numerador_porcentaje = MAXIMO_PORCENTAJE - porcentaje_enajenante
        porcentaje = numerador_porcentaje/MAXIMO_PORCENTAJE
        if ano_inicial1 == ano_inicial2 and rut1 == rut2:
            multipropietario.porcentaje_der *= porcentaje
            break
    return multipropietarios

def agregar_escenario3_cne8(
        formulario, formulario_anterior, propietarios_no_enajenantes,
        enajenantes_fantasma, enajenantes_no_fantasma, adquirentes,
        multipropietarios, mismo_ano, dominio_enajenantes):
    """
    Función que actualiza la lista multipropietarios, agregando propietarios
    no enajenantes, ajustando los enajenantes, y añadiendo el adquirente
    correspondiente según el escenario de compraventa específico.
    """
    if not mismo_ano:
        multipropietarios = agregar_propietarios_no_enajenantes(
            formulario, formulario_anterior,
            multipropietarios, propietarios_no_enajenantes)
        if len(enajenantes_fantasma) > 0:
            persona = enajenantes_fantasma[0]
            estado = ESTADO_FANTASMA
        else:
            persona = enajenantes_no_fantasma[0]
            estado = ESTADO_ANTERIOR
        descuento_porcentaje = MAXIMO_PORCENTAJE - persona.get_porcentaje_der
        numerador_porcentaje = dominio_enajenantes*descuento_porcentaje
        porcentaje_der = numerador_porcentaje/MAXIMO_PORCENTAJE
        # Adición del enajenante.
        multipropietarios = agregar_multipropietario(
            persona.get_rut,
            porcentaje_der,
            formulario,
            formulario_anterior,
            multipropietarios,
            estado)
    else:
        if len(enajenantes_fantasma) <= 0:
            # Disminución del porcentaje de propiedad de enajenantes.
            multipropietarios = reducir_porcentaje_enajenantes(
                multipropietarios, formulario, enajenantes_no_fantasma)
    persona = adquirentes[0]
    if len(enajenantes_fantasma) > 0:  # Enajenante fantasma.
        porcentaje_der = persona.get_porcentaje_der
    else:
        numerador_porcentaje = dominio_enajenantes*persona.get_porcentaje_der
        porcentaje_der = numerador_porcentaje/MAXIMO_PORCENTAJE
    # Adición del adquirente.
    multipropietarios = agregar_multipropietario(
        persona.rut,
        porcentaje_der,
        formulario,
        formulario_anterior,
        multipropietarios,
        ESTADO_ACTUAL)
    return multipropietarios


def obtener_porcentaje_total(multipropietarios):
    """
    Función que suma los porcentajes de derecho positivos de los
    multipropietarios en el último año de vigencia inicial y devuelve
    el total.
    """
    ultimo_ano_inicial = multipropietarios[-1].get_ano_vigencia_inicial
    porcentaje_total = 0
    for multipropietario in multipropietarios:
        ano_inicial = multipropietario.get_ano_vigencia_inicial
        porcentaje_der = multipropietario.get_porcentaje_der
        if (ano_inicial == ultimo_ano_inicial and
            porcentaje_der > MINIMO_PORCENTAJE):
            porcentaje_total += porcentaje_der
    return porcentaje_total


def obtener_cantidad_porcentajes_nulos(multipropietarios):
    """
    Función que cuenta cuántos multipropietarios tienen porcentajes no
    positivos en el último año de vigencia inicial y devuelve esa
    cantidad.
    """
    ultimo_ano_inicial = multipropietarios[-1].get_ano_vigencia_inicial
    cantidad_porcentajes_no_positivos = 0
    for multipropietario in multipropietarios:
        ano_inicial = multipropietario.get_ano_vigencia_inicial
        porcentaje_der = multipropietario.get_porcentaje_der
        if (ano_inicial == ultimo_ano_inicial and
            porcentaje_der <= MINIMO_PORCENTAJE):
            cantidad_porcentajes_no_positivos += 1
    return cantidad_porcentajes_no_positivos


def generar_porcentaje_enajenantes(
        persona_antes, enajenantes_no_fantasma,
        formulario, formulario_anterior,
        multipropietarios, mismo_ano):
    """
    Función que ajusta la lista multipropietarios, agregando o eliminando
    enajenantes según la diferencia en sus porcentajes de derecho.
    """
    for persona in enajenantes_no_fantasma:
        if persona_antes.get_rut == persona.get_rut:
            porcentaje1 = persona_antes.get_porcentaje_der
            porcentaje2 = persona.get_porcentaje_der
            porcentaje_derecho = porcentaje1 - porcentaje2
            if porcentaje_derecho != MINIMO_PORCENTAJE:
                # Adición de enajenantes.
                multipropietarios = agregar_multipropietario(
                    persona.get_rut,
                    porcentaje_derecho,
                    formulario,
                    formulario_anterior,
                    multipropietarios,
                    ESTADO_ANTERIOR)
            elif porcentaje_derecho == MINIMO_PORCENTAJE and not mismo_ano:
                # Eliminación de enajenantes.
                multipropietarios = eliminar_multipropietario(
                formulario, multipropietarios, persona)
    return multipropietarios


def agregar_escenario4_cne8(
        formulario, formulario_anterior, propietarios_enajenantes,
        propietarios_no_enajenantes, enajenantes_fantasma,
        enajenantes_no_fantasma, adquirentes, multipropietarios, mismo_ano):
    """
    Función que actualiza la lista de multipropietarios añadiendo y
    eliminando propietarios y enajenantes según un escenario específico de
    compraventa, y luego agrega los adquirentes correspondientes.
    """
    for persona_antes in propietarios_enajenantes:
        # Generación de propietarios (enajenantes).
        multipropietarios = generar_porcentaje_enajenantes(
            persona_antes, enajenantes_no_fantasma, formulario,
            formulario_anterior, multipropietarios, mismo_ano)
    for persona in enajenantes_fantasma:
        multipropietarios = agregar_multipropietario(
                    persona.get_rut,
                    -persona.get_porcentaje_der,
                    formulario,
                    formulario_anterior,
                    multipropietarios,
                    ESTADO_FANTASMA)
    if not mismo_ano:
        multipropietarios = agregar_propietarios_no_enajenantes(
            formulario, formulario_anterior,
            multipropietarios, propietarios_no_enajenantes)
    else:
        for persona in propietarios_enajenantes:
            # Eliminación de propietarios (enajenantes).
            multipropietarios = eliminar_multipropietario(
                formulario, multipropietarios, persona)
    for persona in adquirentes:
        # Adición de adquirentes.
        multipropietarios = agregar_multipropietario(
            persona.get_rut,
            persona.get_porcentaje_der,
            formulario,
            formulario_anterior,
            multipropietarios,
            ESTADO_ACTUAL)
    return multipropietarios


def agregar_escenarios_cne99(
        formulario, formulario_anterior, formulario_index,
        propietarios, adquirentes, multipropietarios):
    """
    Función que elimina propietarios existentes y agrega nuevos
    adquirentes a la lista de multipropietarios para formularios
    que son de regularización de patrimonio.
    """
    if formulario_index != MINIMO_PORCENTAJE:
        for persona in propietarios:
            multipropietarios = eliminar_multipropietario(
                formulario, multipropietarios, persona)
    for persona in adquirentes:
        multipropietarios = agregar_multipropietario(
            persona.get_rut,
            persona.get_porcentaje_der,
            formulario,
            formulario_anterior,
            multipropietarios,
            ESTADO_ACTUAL)
    return multipropietarios


def actualizar_vigencia_multipropietarios(multipropietarios):
    """
    Función que actualiza los años de vigencia final de los
    multipropietarios y guarda estos cambios en la base de datos.
    """
    ano_inicial_i = multipropietarios[-1].get_ano_vigencia_inicial
    ano_final_i = 0
    cambio = False
    for multipropietario in reversed(multipropietarios):
        if multipropietario.get_ano_vigencia_inicial != ano_inicial_i:
            # Multipropietario con diferente ano_vigencia_inicial
            cambio = True
            ano_inicial_i = multipropietario.get_ano_vigencia_inicial
            ano_final_i = multi_previo.get_ano_vigencia_inicial - 1
        if cambio:
            # Colocación de ano_vigencia_final a multipropietario.
            multipropietario.ano_vigencia_final = ano_final_i
        multi_previo = multipropietario
    # Subida a la base de datos de los multipropietarios.
    for multipropietario in multipropietarios:
        session.add(multipropietario)
        session.commit()


def clasificar_propietarios(multipropietarios,
                            adquirentes,
                            enajenantes, ruts_enajenantes, formulario, formulario_anterior):
    """
    Función que categoriza a los multipropietarios y enajenantes en
    grupos específicos basados en sus RUT y año de vigencia inicial.
    """
    ruts_propietarios_enajenantes = []
    ano_inicial1 = multipropietarios[-1].get_ano_vigencia_inicial
    for multipropietario in multipropietarios:
        ano_inicial2 = multipropietario.get_ano_vigencia_inicial
        if ano_inicial1 == ano_inicial2:
            if multipropietario.get_rut in ruts_enajenantes:
                rut = multipropietario.get_rut
                propietarios_enajenantes.append(multipropietario)
                ruts_propietarios_enajenantes.append(rut)
            else:
                propietarios_no_enajenantes.append(multipropietario)
        propietarios.append(multipropietario)
    for enajenante in enajenantes:
        if enajenante.get_rut in ruts_propietarios_enajenantes:
            enajenantes_no_fantasma.append(enajenante)
        else:
            enajenantes_fantasma.append(enajenante)


def agregar_escenarios_cne8(
        formulario, formulario_anterior, propietarios_no_enajenantes,
        propietarios_enajenantes, enajenantes, enajenantes_fantasma,
        enajenantes_no_fantasma, adquirentes, multipropietarios, mismo_ano,
        dominio_enajenantes, suma_adquirentes):
    """
    Función que elige y aplica el escenario adecuado para actualizar los
    multipropietarios según las características de los adquirentes y
    enajenantes en el formulario.
    """
    if round(suma_adquirentes, 5) == MAXIMO_PORCENTAJE:
        multipropietarios = agregar_escenario1_cne8(
            formulario, formulario_anterior, propietarios_no_enajenantes,
            enajenantes_no_fantasma, adquirentes, multipropietarios,
            mismo_ano, dominio_enajenantes)
    elif round(suma_adquirentes, 5) == MINIMO_PORCENTAJE:
        multipropietarios = agregar_escenario2_cne8(
            formulario, formulario_anterior, propietarios_no_enajenantes,
            enajenantes, adquirentes, multipropietarios,
            mismo_ano, dominio_enajenantes)
    elif len(adquirentes) == UNITARIO and len(enajenantes) == UNITARIO:
        multipropietarios = agregar_escenario3_cne8(
            formulario, formulario_anterior, propietarios_no_enajenantes,
            enajenantes_fantasma, enajenantes_no_fantasma, adquirentes,
            multipropietarios, mismo_ano, dominio_enajenantes)
    else:
        multipropietarios = agregar_escenario4_cne8(
            formulario, formulario_anterior, propietarios_enajenantes,
            propietarios_no_enajenantes, enajenantes_fantasma,
            enajenantes_no_fantasma, adquirentes,
            multipropietarios, mismo_ano)
    return multipropietarios


def obtener_personas(formulario, rol):
    """
    Función que recupera todas las personas de un formulario
    específico con un rol determinado de la base de datos.
    """
    return session.query(PersonaFormulario).filter_by(
        num_atencion=formulario.get_num_atencion,
        rol=rol
    ).all()


def limpiar_multipropietarios(comuna_id, manzana, predio):
    """
    Función que elimina todos los multipropietarios de una comuna,
    manzana y predio específicos de la base de datos, manejando
    posibles errores durante el proceso.
    """
    multipropietarios = session.query(Multipropietario).filter(
        Multipropietario.comuna_id == comuna_id,
        Multipropietario.manzana == manzana,
        Multipropietario.predio == predio
    ).all()
    try:
        # Eliminar cada uno de los multipropietarios encontrados.
        for multipropietario in multipropietarios:
            session.delete(multipropietario)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error al eliminar multipropietarios: {e}")


def procesar_propietarios_repetidos(multipropietarios, rut1,
                                    apariciones, ano_inicial1):
    """
    Función que elimina registros de multipropietarios duplicados y
    consolida sus porcentajes de derechos en un único registro
    """
    if apariciones > 1:
        contador = 0
        porcentaje_der = 0
        for multipropietario in multipropietarios:
            ano_inicial2 = multipropietario.get_ano_vigencia_inicial
            rut2 = multipropietario.get_rut
            if (ano_inicial1 == ano_inicial2 and rut1 == rut2):
                contador +=1
                if contador < apariciones:
                    fecha_ins = multipropietario.get_fecha_ins
                    ano_ins = multipropietario.get_ano_ins
                    num_ins = multipropietario.get_num_ins
                    fojas = multipropietario.get_fojas
                    porcentaje_der += multipropietario.get_porcentaje_der
                    multipropietarios.remove(multipropietario)
                else:
                    multipropietario.fecha_ins = fecha_ins
                    multipropietario.ano_ins = ano_ins
                    multipropietario.num_ins = num_ins
                    multipropietario.fojas = fojas
                    multipropietario.porcentaje_der += porcentaje_der
    return multipropietarios


def agrupar_propietarios_repetidos(multipropietarios):
    """
    Función que cuenta y agrupa registros duplicados de
    multipropietarios por RUT y año de vigencia inicial,
    consolidándolos en registros únicos
    """
    repeticiones = contar_repeticiones(multipropietarios)
    ano_inicial = multipropietarios[-1].get_ano_vigencia_inicial()

    for rut, apariciones in repeticiones.items():
        multipropietarios = procesar_propietarios_repetidos(multipropietarios, rut, apariciones, ano_inicial)

    return multipropietarios

def contar_repeticiones(multipropietarios):
    """
    Función auxiliar que cuenta las repeticiones de multipropietarios por RUT.
    """
    repeticiones = {}
    for multipropietario in multipropietarios:
        rut = multipropietario.get_rut()
        if rut in repeticiones:
            repeticiones[rut] += 1
        else:
            repeticiones[rut] = 1
    return repeticiones

def procesar_propietarios_repetidos(multipropietarios, rut, apariciones, ano_inicial):
    """
    Función auxiliar que procesa multipropietarios repetidos y los consolida en registros únicos.
    """
    multipropietarios_filtrados = []
    for multipropietario in multipropietarios:
        if multipropietario.get_rut() == rut and multipropietario.get_ano_vigencia_inicial() == ano_inicial:
            if apariciones > 1:
                apariciones -= 1
            else:
                multipropietarios_filtrados.append(multipropietario)
        else:
            multipropietarios_filtrados.append(multipropietario)
    return multipropietarios_filtrados



def ordenar_multipropietarios(comuna_id, manzana, predio):
    """
    Función principal que procesa formularios en orden cronológico para añadir objetos
    a la tabla Multipropietarios de una propiedad.
    """
    multipropietarios = obtener_formularios_ordenados(comuna_id, manzana, predio)

    for indice_formulario, formulario in enumerate(multipropietarios):
        formulario_anterior = multipropietarios[indice_formulario - 1] if indice_formulario != 0 else None

        adquirentes = obtener_personas(formulario, 'adquirente')
        enajenantes = obtener_personas(formulario, 'enajenante')
        ruts_enajenantes = [enajenante.get_rut() for enajenante in enajenantes]
        suma_adquirentes = sum(persona.get_porcentaje_der() for persona in adquirentes)

        mismo_ano = es_mismo_ano(formulario, formulario_anterior)

        if indice_formulario != 0:
            clasificar_propietarios(multipropietarios, adquirentes, enajenantes, ruts_enajenantes, formulario, formulario_anterior)
            dominio_enajenantes = calcular_dominio_enajenantes(enajenantes)

        if formulario.cne == CNE_COMPRAVENTA:
            multipropietarios = agregar_escenarios_cne8(formulario, formulario_anterior, adquirentes, enajenantes, ruts_enajenantes, multipropietarios, mismo_ano, dominio_enajenantes, suma_adquirentes)
        else:
            multipropietarios = agregar_escenarios_cne99(formulario, formulario_anterior, indice_formulario, adquirentes, multipropietarios)

        multipropietarios = agrupar_propietarios_repetidos(multipropietarios)

    actualizar_vigencia_multipropietarios(comuna_id, manzana, predio, multipropietarios)

def obtener_formularios_ordenados(comuna_id, manzana, predio):
    """
    Función auxiliar que obtiene formularios ordenados cronológicamente para una propiedad.
    """
    return session.query(Formulario).filter(
        Formulario.comuna_id == comuna_id,
        Formulario.manzana == manzana,
        Formulario.predio == predio
    ).order_by(Formulario.fecha_ins).all()

def es_mismo_ano(formulario_actual, formulario_anterior):
    """
    Función auxiliar que verifica si dos formularios tienen el mismo año de inscripción.
    """
    if formulario_anterior:
        return formulario_actual.get_fecha_ins().year == formulario_anterior.get_fecha_ins().year
    return False

def calcular_dominio_enajenantes(enajenantes):
    """
    Función auxiliar que calcula el dominio de los enajenantes basado en sus porcentajes de derecho.
    """
    return sum(enajenante.get_porcentaje_der() for enajenante in enajenantes)


def crear_tablas():
    Base.metadata.create_all(session.bind)
    session.close()


app = Flask(__name__)
app.secret_key = LLAVE
crear_tablas()


@app.route('/')
def mostrar_pagina_principal():
    return render_template(f'{HOME_PAGE}')


def generar_numero_atencion():
    """
    Función que genera un número de atención de 9 dígitos
    que es único en la base de datos.
    """
    while True:
        numero_atencion = ''.join(choices(digits, k=9))
        formulario_existente = session.query(Formulario).filter_by(
            num_atencion=numero_atencion).first()
        if not formulario_existente:
            return numero_atencion


@app.route('/enviar_flash', methods=['POST'])
def enviar_flash():
    """
    Función que permite emitir una alerta después de cargar un archivo.
    """
    mensaje = request.form['message']
    categoria = request.form['category']
    flash(mensaje, categoria)
    return 'OK'


@app.route('/comunas/<int:region_id>')
def obtener_comunas(region_id):
    comunas = session.query(Comuna).filter_by(
        region_id=region_id
    ).all()
    comunas_data = []
    for comuna in comunas:
        comunas_data.append({'id': comuna.get_id,
                             'nombre': comuna.get_nombre})
    return jsonify(comunas_data)


@app.route('/formularios')
def mostrar_formularios():
    formularios = session.query(Formulario).all()
    return render_template('show_formularios.html',
                           formularios=formularios)


@app.route('/formularios/<string:num_atencion>')
def mostrar_formulario(num_atencion):
    """
    Función que muestra un formulario específico en la página,
    obteniéndolo de la base de datos según el número de atención
    proporcionado.
    """
    formulario = session.query(Formulario).filter_by(
        num_atencion=num_atencion).first()
    return render_template('index_formulario.html',
                           formulario=formulario)


@app.route('/nuevo_formulario', methods=['GET'])
def nuevo_formulario():
    """
    Función que prepara y muestra la página para crear un nuevo
    formulario, generando un número de atención único y
    obteniendo las regiones de la base de datos.
    """
    num_atencion = generar_numero_atencion()
    regiones = session.query(Region).all()
    return render_template('new_formulario.html',
                           num_atencion=num_atencion,
                           regiones=regiones)


@app.route('/enviar_formulario', methods=['POST'])
def enviar_formulario():
    """
    Función que crea un nuevo formulario y sus registros asociados en la
    base de datos, ordenando los multipropietarios.
    """
    num_atencion = str(request.form.get('num_atencion'))
    cne = int(request.form.get('cne'))
    comuna_id = int(request.form.get('comuna'))
    manzana = int(request.form.get('manzana'))
    predio = int(request.form.get('predio'))
    fojas = int(request.form.get('fojas'))
    fecha_ins = datetime.strptime(request.form.get('fecha_ins'),
                                  '%Y-%m-%dT%H:%M')
    num_ins = int(request.form.get('num_ins'))
    crear_formulario(num_atencion, cne, comuna_id, manzana, predio, fojas,
                     fecha_ins, num_ins)
    for tipo in ['enajenante', 'adquirente']:
        rut_list = request.form.getlist(f'{tipo}_rut[]')
        porcentaje_list = request.form.getlist(f'{tipo}_porcentaje[]')
        for rut, porcentaje in zip(rut_list, porcentaje_list):
            crear_persona_formulario(rut,
                                     num_atencion,
                                     porcentaje,
                                     tipo)
    session.commit()
    ordenar_multipropietarios(comuna_id, manzana, predio)
    flash("¡Formulario creado con éxito!", 'success')
    return render_template(f'{HOME_PAGE}')


@app.route('/cargar_archivo', methods=['GET'])
def mostrar_carga_archivo():
    return render_template("upload_formulario.html")


def procesar_formulario(num_atencion, form):
    """
    Función que valida y crea registros de un formulario en la base de datos y
    maneja posibles errores durante el proceso.
    """
    try:
        cne = int(form["CNE"])
        comuna_id = int(form["bienRaiz"]["comuna"])
        comunas = session.query(Comuna).all()
        comunas_ids = [com.get_id for com in comunas]
        if comuna_id in comunas_ids:
            manzana = int(form["bienRaiz"]["manzana"])
            predio = int(form["bienRaiz"]["predio"])
            fojas = int(form["fojas"])
            fecha_ins = datetime.strptime(form['fechaInscripcion'], '%Y-%m-%d')
            num_ins = form["nroInscripcion"]
            crear_formulario(num_atencion, cne, comuna_id, manzana, predio,
                                fojas, fecha_ins, num_ins)
            # Recorrido de los adquirentes del formulario en cuestión.
            if "adquirentes" in form:
                for adquirente in form["adquirentes"]:
                    crear_persona_formulario(
                        adquirente["RUNRUT"].replace(".", ""),
                        num_atencion,
                        adquirente["porcDerecho"],
                        "adquirente"
                    )
            # Recorrido de los enajenantes del formulario en cuestión.
            if "enajenantes" in form:
                for enajenante in form["enajenantes"]:
                    crear_persona_formulario(
                        enajenante["RUNRUT"].replace(".", ""),
                        num_atencion,
                        enajenante["porcDerecho"],
                        "enajenante"
                    )
            session.commit()
            return [comuna_id, manzana, predio]
    except (KeyError, ValueError, TypeError, SQLAlchemyError) as e:
        print("Hubo un error creando el formulario:", e)
    return None


@app.route('/cargar_archivo', methods=['POST'])
def subir_archivo():
    """
    Función que carga y procesa un archivo JSON, creando formularios y
    actualizando la tabla Multipropietarios en la base de datos.
    """
    if 'JSONfile' not in request.files:
        flash("No se envió ningún archivo", 'danger')
        return 'No se envió ningún archivo.'
    file = request.files['JSONfile']
    file_content = file.read()
    try:
        json_dict = loads(file_content)
        terrenos = []
        # Extraemos los formularios presentes en el archivo JSON.
        for file_id in json_dict:
            for form in json_dict[file_id]:
                num_atencion = generar_numero_atencion()
                terreno = procesar_formulario(num_atencion, form)
                if terreno and terreno not in terrenos:
                    terrenos.append(terreno)
        for terreno in terrenos:
            limpiar_multipropietarios(terreno[0], terreno[1], terreno[2])
            ordenar_multipropietarios(terreno[0], terreno[1], terreno[2])
        flash("Archivo cargado con éxito", 'success')
    except JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
    return render_template(f'{HOME_PAGE}')


@app.route('/filtrar_multipropietarios')
def filtrar_multipropietarios():
    """
    Función que permite obtener todas las regiones de la base de datos y
    mostrar la página de filtración de multipropietarios con la información.
    """
    regiones = session.query(Region).all()
    return render_template('filter_multipropietario.html', regiones=regiones)


@app.route('/buscar_multipropietarios')
def buscar_multipropietarios():
    """
    Función que busca y devuelve multipropietarios en formato JSON según
    los criterios especificados en la solicitud.
    """
    comuna_id = request.args.get('comuna_id')
    manzana = request.args.get('manzana')
    predio = request.args.get('predio')
    ano = request.args.get('ano')
    # Filtramos la tabla Multipropietario.
    multipropietarios = session.query(Multipropietario).filter(
        Multipropietario.comuna_id == comuna_id,
        Multipropietario.manzana == manzana,
        Multipropietario.predio == predio,
    ).filter(
        Multipropietario.ano_vigencia_inicial <= ano,
        (Multipropietario.ano_vigencia_final >= ano) |
        (Multipropietario.ano_vigencia_final == None) # pylint: disable=singleton-comparison
    ).all()
    # Los datos son convertidos a un formato adecuado para la respuesta JSON.
    multipropietarios_data = []
    for multipropietario in multipropietarios:
        multipropietarios_data.append({
            'comuna_id': multipropietario.get_comuna_id,
            'manzana': multipropietario.get_manzana,
            'predio': multipropietario.get_predio,
            'fecha_ins': None if multipropietario.get_fecha_ins is None
            else multipropietario.get_fecha_ins.strftime('%Y-%m-%d'),
            'ano_ins': multipropietario.get_ano_ins,
            'num_ins': multipropietario.get_num_ins,
            'fojas': multipropietario.get_fojas,
            'rut': multipropietario.get_rut,
            'porcentaje_der': multipropietario.get_porcentaje_der,
            'ano_vigencia_inicial': multipropietario.get_ano_vigencia_inicial,
            'ano_vigencia_final': multipropietario.get_ano_vigencia_final
        })
    return jsonify(multipropietarios_data)

if __name__ == '__main__':
    app.run(debug=True, port=4000)
