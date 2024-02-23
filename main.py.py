from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit
import pyodbc
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your secret key'  # Asegúrate de establecer una clave secreta para las sesiones
socketio = SocketIO(app)

new_data = []  # Almacena los nuevos datos

def get_db_connection():
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=HospitalDB;Trusted_Connection=yes')
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    print("Database connection verified:", cursor.fetchone())
    return conn, cursor

@app.route('/')
def index():
    return render_template('index.html.html')

@app.route('/ingresar', methods=['GET', 'POST'])
def ingresar():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        cuarto = request.form.get('cuarto')
        camilla = request.form.get('camilla')
        especialidad = request.form.get('especialidad')
        conn, cursor = get_db_connection()
        id = None
        try:
            cursor.execute("INSERT INTO dbo.Pacientes (Nombre, Cuarto, Camilla, Especialidad) OUTPUT INSERTED.ID VALUES (?, ?, ?, ?)", (nombre, cuarto, camilla, especialidad))
            id = cursor.fetchone()[0]
            conn.commit()
            print("Datos insertados en la base de datos:", id, nombre, cuarto, camilla, especialidad)
        except pyodbc.Error as ex:
            print("Ocurrió un error al intentar insertar los datos:", ex)
        finally:
            conn.close()
        if id is not None:
            data = {'ID': id, 'Nombre': nombre, 'Cuarto': cuarto, 'Camilla': camilla, 'Especialidad': especialidad}
            new_data.append(data)  # Añade los nuevos datos a la lista
            session['new_data'] = new_data  # Almacena los nuevos datos en la sesión
            socketio.emit('update data', data)
            print("Datos enviados a través de Socket.IO:", data)

            # Añade la fecha actual a los datos
            data['Fecha'] = datetime.now()

            # Carga los datos existentes del archivo de Excel
            try:
                df = pd.read_excel('datos.xlsx')
            except FileNotFoundError:
                df = pd.DataFrame()
            except Exception as e:
                print("Ocurrió un error al intentar leer el archivo 'datos.xlsx':", e)
                df = pd.DataFrame()

            # Añade los nuevos datos al final del DataFrame
            df = pd.concat([df, pd.DataFrame([data])])

            # Guarda los datos en el archivo de Excel
            df.to_excel('datos.xlsx', index=False)
        return redirect(url_for('ingresar'))  # Redirige a ingresar.html
    return render_template('ingresar.html')

@app.route('/editar', methods=['GET', 'POST'])
def editar():
    if request.method == 'POST':
        id = request.form.get('id')
        nombre = request.form.get('nombre')
        cuarto = request.form.get('cuarto')
        camilla = request.form.get('camilla')
        especialidad = request.form.get('especialidad')
        conn, cursor = get_db_connection()
        try:
            cursor.execute("UPDATE dbo.Pacientes SET Nombre = ?, Cuarto = ?, Camilla = ?, Especialidad = ? WHERE ID = ?", (nombre, cuarto, camilla, especialidad, id))
            conn.commit()
            print("Datos actualizados en la base de datos:", id, nombre, cuarto, camilla, especialidad)
        except pyodbc.Error as ex:
            print("Ocurrió un error al intentar actualizar los datos:", ex)
        finally:
            conn.close()
        data = {'ID': id, 'Nombre': nombre, 'Cuarto': cuarto, 'Camilla': camilla, 'Especialidad': especialidad}
        socketio.emit('update data', data)
        socketio.emit('renumber', data['Especialidad'])  # Emitir un evento 'renumber' para renumerar las filas

        # Actualizar los datos en la sesión
        new_data = session.get('new_data', [])
        for i, d in enumerate(new_data):
            if d['ID'] == id:
                new_data[i] = data
                break
        session['new_data'] = new_data

        return redirect(url_for('editar', _external=True, _scheme='http'))  # Redirige a editar.html y fuerza una recarga de la página
    else:
        new_data = session.get('new_data', [])  # Recupera los nuevos datos de la sesión
        return render_template('editar.html', data=new_data)

@app.route('/editar_post', methods=['POST'])
def editar_post():
    id = request.form.get('id')
    nombre = request.form.get('nombre')
    cuarto = request.form.get('cuarto')
    camilla = request.form.get('camilla')
    especialidad = request.form.get('especialidad')
    conn, cursor = get_db_connection()
    try:
        cursor.execute("UPDATE dbo.Pacientes SET Nombre = ?, Cuarto = ?, Camilla = ?, Especialidad = ? WHERE ID = ?", (nombre, cuarto, camilla, especialidad, id))
        conn.commit()
        print("Datos actualizados en la base de datos:", id, nombre, cuarto, camilla, especialidad)
    except pyodbc.Error as ex:
        print("Ocurrió un error al intentar actualizar los datos:", ex)
    finally:
        conn.close()
    data = {'ID': id, 'Nombre': nombre, 'Cuarto': cuarto, 'Camilla': camilla, 'Especialidad': especialidad}
    socketio.emit('update data', data)
    socketio.emit('renumber', data['Especialidad'])  # Emitir un evento 'renumber' para renumerar las filas
    return redirect(url_for('editar', _external=True, _scheme='http'))  # Redirige a editar.html

@app.route('/get_data', methods=['GET'])
def get_data():
    # Recupera los nuevos datos de la sesión
    new_data = session.get('new_data', [])
    return jsonify(new_data)

@socketio.on('delete data')
def handle_delete(data):
    id = data['id']
    conn, cursor = get_db_connection()
    try:
        cursor.execute("DELETE FROM dbo.Pacientes WHERE ID = ?", (id,))
        conn.commit()
        print("Datos borrados de la base de datos:", id)
    except pyodbc.Error as ex:
        print("Ocurrió un error al intentar borrar los datos:", ex)
    finally:
        conn.close()

    #Emitir un evento de Socket.IO a todos los clientes para informarles de la eliminación
    socketio.emit('delete data', id)

if __name__ == '__main__':
    socketio.run(app)
