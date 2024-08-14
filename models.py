from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship, declarative_base

# Crea una clase base para definiciones de modelos.
Base = declarative_base()


class Region(Base):
    __tablename__ = 'region'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)

    comuna = relationship("Comuna", back_populates="region")


class Comuna(Base):
    __tablename__ = 'comuna'

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey('region.id'), nullable=False)
    nombre = Column(String(100), nullable=False)

    formulario = relationship("Formulario", back_populates="comuna")
    region = relationship("Region", back_populates="comuna")
    multipropietario = relationship("Multipropietario",
                                    back_populates="comuna")

    # Getters
    @property
    def get_id(self):
        return self.id

    @property
    def get_nombre(self):
        return self.nombre


class Formulario(Base):
    __tablename__ = 'formulario'

    num_atencion = Column(String(9), primary_key=True)
    cne = Column(Integer, nullable=False)
    comuna_id = Column(Integer, ForeignKey('comuna.id'), nullable=False)
    manzana = Column(Integer, nullable=False)
    predio = Column(Integer, nullable=False)
    fojas = Column(Integer, nullable=False)
    fecha_ins = Column(DateTime, nullable=False)
    num_ins = Column(Integer, nullable=False)

    persona_formulario = relationship("PersonaFormulario",
                                      back_populates="formulario")
    comuna = relationship("Comuna", back_populates="formulario")

    # Getters
    @property
    def get_fecha_ins(self):
        return self.fecha_ins

    @property
    def get_comuna_id(self):
        return self.comuna_id

    @property
    def get_manzana(self):
        return self.manzana

    @property
    def get_predio(self):
        return self.predio

    @property
    def get_fojas(self):
        return self.fojas

    @property
    def get_num_ins(self):
        return self.num_ins

    @property
    def get_num_atencion(self):
        return self.num_atencion


class PersonaFormulario(Base):
    __tablename__ = 'persona_formulario'

    rut = Column(String(255), primary_key=True)
    num_atencion = Column(String(255),
                          ForeignKey('formulario.num_atencion'),
                          primary_key=True)
    rol = Column(String(255), primary_key=True)
    porcentaje_der = Column(Float, nullable=False)

    formulario = relationship("Formulario",
                              back_populates="persona_formulario")

    # Getters
    @property
    def get_rut(self):
        return self.rut

    @property
    def get_porcentaje_der(self):
        return self.porcentaje_der


class Multipropietario(Base):
    __tablename__ = 'multipropietario'

    id = Column(Integer, primary_key=True, autoincrement=True)

    rut = Column(String(255), nullable=False)
    comuna_id = Column(Integer, ForeignKey('comuna.id'), nullable=False)
    manzana = Column(Integer, nullable=False)
    predio = Column(Integer, nullable=False)
    fecha_ins = Column(DateTime)

    porcentaje_der = Column(Float, nullable=False)
    fojas = Column(Integer)
    ano_ins = Column(Integer)
    num_ins = Column(Integer)
    ano_vigencia_inicial = Column(Integer)
    ano_vigencia_final = Column(Integer)

    comuna = relationship("Comuna", back_populates="multipropietario")

    # Getters
    @property
    def get_rut(self):
        return self.rut

    @property
    def get_porcentaje_der(self):
        return self.porcentaje_der

    @property
    def get_ano_vigencia_inicial(self):
        return self.ano_vigencia_inicial

    @property
    def get_ano_vigencia_final(self):
        return self.ano_vigencia_final

    @property
    def get_fecha_ins(self):
        return self.fecha_ins

    @property
    def get_comuna_id(self):
        return self.comuna_id

    @property
    def get_manzana(self):
        return self.manzana

    @property
    def get_predio(self):
        return self.predio

    @property
    def get_fojas(self):
        return self.fojas

    @property
    def get_num_ins(self):
        return self.num_ins
    
    @property
    def get_ano_ins(self):
        return self.ano_ins

    @property
    def get_num_atencion(self):
        return self.num_atencion
