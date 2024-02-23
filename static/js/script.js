var socket = io();
var tables = {}; // Almacena todas las tablas por especialidad
var tableContainer = $('#tables-container'); // Contenedor de las tablas
var counts = {}; // Contador para la numeración de cada especialidad

socket.on('update data', function(data) {
    console.log(data); // Imprime los datos recibidos en la consola

    // Buscamos la tabla de esta especialidad
    var table = tables[data.Especialidad];
    
    // Si la tabla no existe, la creamos
    if (!table) {
        table = $('<table></table>');
        table.attr('id', 'table-' + data.Especialidad);
        // Agregamos un encabezado a la tabla
        var thead = $('<thead></thead>');
        var headerRow = $('<tr></tr>');
        ['Número', 'Nombre', 'Cuarto', 'Camilla', 'Especialidad'].forEach(function(header) {
            var th = $('<th></th>');
            th.text(header);
            headerRow.append(th);
        });
        thead.append(headerRow);
        table.append(thead);

        $('#tables-container').append(table);
        tables[data.Especialidad] = table; // Guardamos la tabla en el objeto tables
        counts[data.Especialidad] = 0; // Inicializamos el contador para esta especialidad
    }
    
    // Eliminamos el dato antiguo de la tabla
    $('#row-' + data.ID).remove();

    // Ahora, agregamos los datos a la tabla
    var row = $('<tr></tr>');
    row.attr('id', 'row-' + data.ID);

    var cell0 = $('<td></td>'); // Celda para la numeración
    var cell1 = $('<td></td>');
    var cell2 = $('<td></td>');
    var cell3 = $('<td></td>');
    var cell4 = $('<td></td>');

    cell0.text(++counts[data.Especialidad]); // Incrementamos el contador de esta especialidad y lo agregamos a la celda
    cell1.text(data.Nombre);
    cell2.text(data.Cuarto);
    cell3.text(data.Camilla);
    cell4.text(data.Especialidad);

    row.append(cell0, cell1, cell2, cell3, cell4);
    table.append(row);

    // Mostramos la tabla
    table.show();
});

socket.on('delete data', function(data_id) {
    // Eliminar la fila correspondiente de la tabla
    $('#row-' + data_id).remove();
    --counts[data.especialidad]; // Decrementamos el contador de esta especialidad
});

function deleteRow(button) {
    var data_id = $(button).data('id');
    var especialidad = $(button).data('especialidad');
    socket.emit('delete data', {id: data_id, especialidad: especialidad});
    $(button).closest('tr').remove();
}

// Función para desplazar las tablas
function scrollTables() {
    var speed = 2; // Ajusta la velocidad de desplazamiento aquí
    var container = $('#tables-container');
    container.scrollTop(container.scrollTop() + speed);
    if (container[0].scrollHeight - container.scrollTop() <= container.outerHeight()) {
        container.scrollTop(0);
    }
    requestAnimationFrame(scrollTables);
}
requestAnimationFrame(scrollTables);

socket.on('renumber', function(especialidad) {
    // Buscar la tabla de esta especialidad
    var table = $('#table-' + especialidad);
    // Renumerar las filas de la tabla
    table.find('tr').each(function(index, row) {
        if (index > 0) {  // Ignorar la fila del encabezado
            $(row).find('td:first').text(index);
        }
    });
});
