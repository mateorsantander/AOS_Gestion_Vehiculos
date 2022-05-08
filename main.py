import json

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_cors import CORS, cross_origin
import re

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound



app = Flask(__name__)

##CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicles.db'
app.config['OPENAPI_VERSION'] = '3.0.2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)




##CREATE TABLE
class Vehicle(db.Model):
    VIN = db.Column(db.String, primary_key=True, unique=True)
    matricula_actual = db.Column(db.String(250), nullable=False)
    matriculas_anteriores = db.Column(db.String(250), nullable=True)
    tipo_de_vehiculo = db.Column(db.String(250), nullable=False)
    kilometraje = db.Column(db.Integer, nullable=True)
    marca = db.Column(db.String(250), nullable=False)
    modelo = db.Column(db.String(250), nullable=False)
    CV = db.Column(db.Integer, nullable=True)
    anio_fabricacion = db.Column(db.Integer, nullable=True)
    tipo_de_combustible = db.Column(db.String(250), nullable=False)
    distintivo_ambiental = db.Column(db.String(250), nullable=True)
    tamanio_deposito = db.Column(db.Integer, nullable=True)
    motor = db.Column(db.String(250), nullable=True)
    peso = db.Column(db.Integer, nullable=True)
    dimensiones = db.Column(db.String(250), nullable=True)

    coche = relationship("Coche", backref="vehiculo", uselist=False, cascade="all,delete")
    moto = relationship("Moto", backref="vehiculo", uselist=False, cascade="all,delete")
    camion = relationship("Camion", backref="vehiculo", uselist=False, cascade="all,delete")

    def to_dict(self):
        string1 = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        string1["links"] = {
            "self": f"/api/v1/vehiculos/{string1['VIN']}",
            "parent": "/api/v1/vehiculos/"
        }
        if self.coche != None :
            string2 ={column.name: getattr(self.coche, column.name) for column in self.coche.__table__.columns}
            string1.update({'extra_tipo_de_vehiculo': string2})
        if self.moto != None :
            string2 ={column.name: getattr(self.moto, column.name) for column in self.moto.__table__.columns}
            string1.update({'extra_tipo_de_vehiculo': string2})
        if self.camion != None :
            string2 ={column.name: getattr(self.camion, column.name) for column in self.camion.__table__.columns}
            string1.update({'extra_tipo_de_vehiculo': string2})
        return string1

class Coche(db.Model):
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    numeroPuertas = db.Column(db.Integer, nullable=True)
    numeroDePlazas = db.Column(db.Integer, nullable=True)
    vehicle_id = db.Column(db.String, db.ForeignKey('vehicle.VIN'))


class Moto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    centimetrosCubicos = db.Column(db.Integer, nullable=True)
    vehicle_id = db.Column(db.String, db.ForeignKey('vehicle.VIN'))


class Camion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String, nullable=True)
    vehicle_id = db.Column(db.String, db.ForeignKey('vehicle.VIN'))

db.create_all()


@app.route("/api/v1/vehiculos", methods=["GET"])
def cget():
    order = request.args.get("order")
    ordering = request.args.get("ordering")
    if order == None:
        vehicles = db.session.query(Vehicle).all()
    elif order == "VIN":
        if ordering == "DESC":
            vehicles = db.session.query(Vehicle).order_by(Vehicle.VIN.desc()).all()
        else:
            vehicles = db.session.query(Vehicle).order_by(Vehicle.VIN.asc()).all()
    elif order == "modelo":
        if ordering == "DESC":
            vehicles = db.session.query(Vehicle).order_by(Vehicle.modelo.desc()).all()
        else:
            vehicles = db.session.query(Vehicle).order_by(Vehicle.modelo.asc()).all()
    if len(vehicles) == 0:
        return jsonify(type="https://httpstatuses.com/412", title="NOT FOUND", status=404,
                       detail="El recurso solicitado no está disponible.", instance="about:blank"), 404
    return jsonify([vehicle.to_dict() for vehicle in vehicles]), 200

@app.route("/api/v1/vehiculos", methods=["POST"])
def post():
    try:
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            json_veh = request.json
            if(comprobar_VIN(json_veh.get("VIN")) and comprobar_TDC(json_veh.get("tipo_de_combustible")) and comprobar_TDV(json_veh.get("tipo_de_vehiculo")) and comprobar_DT_U(json_veh.get("distintivo_ambiental"))):
                new_vehicle = Vehicle(VIN=json_veh.get("VIN"), matricula_actual=json_veh.get("matricula_actual"),tipo_de_vehiculo=json_veh.get("tipo_de_vehiculo"),marca=json_veh.get("marca"),modelo=json_veh.get("modelo"),tipo_de_combustible =json_veh.get("tipo_de_combustible"))
                new_vehicle.matriculas_anteriores = list_to_list_string(json_veh.get("matriculas_anteriores"))
                new_vehicle.kilometraje = json_veh.get("kilometraje")
                new_vehicle.CV = json_veh.get("CV")
                new_vehicle.anio_fabricacion = json_veh.get("anio_fabricacion")
                new_vehicle.distintivo_ambiental = json_veh.get("distintivo_ambiental")
                new_vehicle.tamanio_deposito = json_veh.get("tamanio_deposito")
                new_vehicle.motor = json_veh.get("motor")
                new_vehicle.peso = json_veh.get("peso")
                new_vehicle.dimensiones = json_veh.get("dimensiones")
                db.session.add(new_vehicle)
                db.session.commit()
                if new_vehicle.tipo_de_vehiculo == "Coche" and json_veh.get("extra_tipo_de_vehiculo")!=None:
                    extra = json_veh.get("extra_tipo_de_vehiculo")
                    new_car = Coche(numeroPuertas=extra.get("numeroDePuertas"), numeroDePlazas=extra.get("numeroDePlazas"))
                    db.session.add(new_car)
                    db.session.commit()
                    new_vehicle.coche = new_car
                    db.session.commit()

                if new_vehicle.tipo_de_vehiculo == "Moto" and json_veh.get("extra_tipo_de_vehiculo")!=None:
                    extra = json_veh.get("extra_tipo_de_vehiculo")
                    print(extra.get("centimetrosCubicos"))


                    new_car = Moto(centimetrosCubicos=extra.get("centimetrosCubicos"))
                    db.session.add(new_car)
                    db.session.commit()
                    new_vehicle.moto = new_car
                    db.session.commit()

                if new_vehicle.tipo_de_vehiculo == "Camion" and json_veh.get("extra_tipo_de_vehiculo")!=None:
                    extra = json_veh.get("extra_tipo_de_vehiculo")

                    new_car = Camion(descripcion=extra.get("descripcion"))
                    db.session.add(new_car)
                    db.session.commit()
                    new_vehicle.camion = new_car
                    db.session.commit()


                return jsonify(vehicle=new_vehicle.to_dict()), 201

        return jsonify(type="https://httpstatuses.com/422", title="UNPROCESSABLE ENTITY", status=422, detail="Ausencia de atributos obligatorios (VIN, modelo, matricula_actual, tipo_de_vehiculo, marca, tipo_de_combustible), falla en el formato o existe un coche con el mismo VIN.", instance="about:blank"), 422
    except:
        return jsonify(type="https://httpstatuses.com/422", title="UNPROCESSABLE ENTITY", status=422,
                       detail="Ausencia de atributos obligatorios (VIN, modelo, matricula_actual, tipo_de_vehiculo, marca, tipo_de_combustible), falla en el formato o existe un coche con el mismo VIN.",
                       instance="about:blank"), 422


@app.route("/api/v1/vehiculos", methods=["OPTIONS"]) #No funciona
def options():
    resp = flask.Response("")
    resp.headers['Access-Control-Allow-Origin'] =  'http://127.0.0.1:5000/'
    resp.headers['access-control-allow-headers'] =  '*'
    resp.headers['access-control-expose-headers'] = '*'
    resp.headers['access-control-allow-credentials'] = 'True'
    resp.headers['allow'] = 'GET,POST,OPTIONS '
    return resp, 204

@app.route("/api/v1/vehiculos/<string:VIN>", methods=["DELETE"])
def delete(VIN):
    try:
        vehicle = db.session.query(Vehicle).filter_by(VIN=VIN).one()
    except MultipleResultsFound :
        msg = "Hay más de un vehículo con ese VIN. Se borra el primero"
        vehicle = db.session.query(Vehicle).filter_by(VIN=VIN).first()
        db.session.delete(vehicle)
        db.session.commit()
        return jsonify(detail=msg), 200
    except NoResultFound:
        return jsonify(type="https://httpstatuses.com/404", title="NOT FOUND", status=404,
                       detail="El recurso solicitado no está disponible.", instance="about:blank"), 404

    else:
        msg="vehiculo eliminado"
        db.session.delete(vehicle)
        db.session.commit()
        return jsonify(detail=msg), 200


@app.route("/api/v1/vehiculos/<string:VIN>", methods=["GET"])
def get(VIN):
    vehicle = db.session.query(Vehicle).filter_by(VIN=VIN).first()
    if vehicle:
        return jsonify(vehicle=vehicle.to_dict()), 200
    else:
        return jsonify(type="https://httpstatuses.com/412", title="NOT FOUND", status=404,
                       detail="El recurso solicitado no está disponible.", instance="about:blank"), 404


@app.route("/api/v1/vehiculos/<string:VIN>", methods=["PUT"])
def put(VIN):
    vehicle = db.session.query(Vehicle).filter_by(VIN=VIN).first()
    if vehicle:
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            json_veh = request.json
            if(comprobar_TDC_U(json_veh.get("tipo_de_combustible")) and comprobar_TDV_U(json_veh.get("tipo_de_vehiculo")) and comprobar_DT_U(json_veh.get("distintivo_ambiental"))):
                vehicle.matricula_actual = json_veh.get("matricula_actual") or vehicle.matricula_actual
                vehicle.matriculas_anteriores = list_to_list_string(json_veh.get("matriculas_anteriores")) or vehicle.matriculas_anteriores
                vehicle.tipo_de_vehiculo = json_veh.get("tipo_de_vehiculo") or vehicle.tipo_de_vehiculo
                vehicle.kilometraje = json_veh.get("kilometraje") or vehicle.kilometraje
                vehicle.marca = json_veh.get("marca") or vehicle.marca
                vehicle.modelo = json_veh.get("modelo") or vehicle.modelo
                vehicle.CV = json_veh.get("CV") or vehicle.CV
                vehicle.anio_fabricacion = json_veh.get("anio_fabricacion") or vehicle.anio_fabricacion
                vehicle.tipo_de_combustible = json_veh.get("tipo_de_combustible") or vehicle.tipo_de_combustible
                vehicle.distintivo_ambiental = json_veh.get("distintivo_ambiental") or vehicle.distintivo_ambiental
                vehicle.tamanio_deposito = json_veh.get("tamanio_deposito") or vehicle.tamanio_deposito
                vehicle.motor = json_veh.get("motor") or vehicle.motor
                vehicle.peso = json_veh.get("peso") or vehicle.peso
                vehicle.dimensiones = json_veh.get("dimensiones") or vehicle.dimensiones

                db.session.commit()
                return jsonify(vehicle=vehicle.to_dict()), 200
            else:
                return jsonify(type="https://httpstatuses.com/422", title="UNPROCESSABLE ENTITY", status=422,
                               detail="Falla en el formato de los enumerados.",
                               instance="about:blank"), 422


    return jsonify(type= "https://httpstatuses.com/412", title = "NOT FOUND", status= 404, detail = "El recurso solicitado no está disponible.",instance= "about:blank"), 404

@app.route("/api/v1/vehiculos/<string:VIN>", methods=["OPTIONS"]) #No funciona
def options_VIN(VIN):
    resp = flask.Response("")
    resp.headers['Access-Control-Allow-Origin'] =  'http://127.0.0.1:5000/'
    resp.headers['access-control-allow-headers'] =  '*'
    resp.headers['access-control-expose-headers'] = '*'
    resp.headers['access-control-allow-credentials'] = 'True'
    resp.headers['allow'] = 'GET,PUT,OPTIONS'
    return resp, 204


@app.route("/prueba")
def valores_prueba():
    #Insercion de varios
    car1 = Vehicle(VIN="1234567", matricula_actual="BBBB",tipo_de_vehiculo="AAAA",marca="s",modelo="A",tipo_de_combustible = " ")
    car2 = Vehicle(VIN="1231234", matricula_actual="BBBB",tipo_de_vehiculo="AAAA",marca="s",modelo="B",tipo_de_combustible = " ")
    db.session.add(car1)
    db.session.add(car2)
    db.session.commit()
    return jsonify(ola = {"ole"})


def list_to_list_string(lista):
    if isinstance(lista, str):
        return lista
    elif lista:
        print(type(lista))
        string_list ="["
        for i in range(len(lista)):
            string_list += lista[i]
            if i != (len(lista) - 1):
                string_list += ", "
        string_list += "]"
        print(string_list)
        return string_list
    else:
        return None




def comprobar_VIN(VIN):
    result = re.search("[A-Ha-hJ-Nj-nPpR-Tr-tV-Yv-y1-9]{1}[0-9]{6}", VIN)
    if result:
        return True
    else:
        return False
def comprobar_TDC(TDC):
    lista = [ "Gasolina", "Gasoleo o Diesel", "Eléctrico", "Híbrido Gasolina-Eléctrico", "Híbrido Gasolina-Gas licuado", "Híbrido Gasolina-Gas natural", "Híbrido Gasoleo-Eléctrico", "Híbrido Gasoleo-Gas licuado", "Híbrido Gasoleo-Gas natural"]
    enumLower = [s.lower() for s in lista]
    result = TDC.lower() in enumLower
    return result

def comprobar_TDV(TDV):
    result = TDV in ["Coche", "Moto", "Camion"]

    return result

def comprobar_DT(DT):
    result = DT in [ "Categoría 0 Emisiones", "Categoría Eco", "Categoría C", "Categoría B", "Categoría A" ]

    return result

def comprobar_TDC_U(TDC):
    result = TDC == None or comprobar_TDC(TDC)
    return result

def comprobar_TDV_U(TDV):
    result = TDV == None or comprobar_TDV(TDV)
    return result
def comprobar_DT_U(DT):
    result = DT == None or comprobar_DT(DT)
    return result

if __name__ == '__main__':
    app.run(host="0.0.0.0")
