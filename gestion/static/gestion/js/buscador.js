document.addEventListener('DOMContentLoaded', function () {
    const inputBusqueda = document.getElementById('input-busqueda');
    const contenedorResultados = document.getElementById('contenedor-resultados');
    let temporizadorDebounce;

    // Escuchar cada vez que el usuario teclea algo
    inputBusqueda.addEventListener('input', function () {
        // Limpiar el temporizador anterior si el usuario sigue tecleando
        clearTimeout(temporizadorDebounce);

        const query = this.value.trim();

        // Si borró todo el texto, restauramos el mensaje inicial
        if (query.length === 0) {
            contenedorResultados.innerHTML = `
                <div class="text-center text-muted mt-5">
                    <p>Ingrese un término de búsqueda para comenzar.</p>
                </div>`;
            return;
        }

        // Indicador visual de carga
        contenedorResultados.innerHTML = `
            <div class="text-center text-muted mt-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Buscando...</span>
                </div>
                <p class="mt-2">Buscando registros...</p>
            </div>`;

        // Esperar 300 milisegundos después de que termine de teclear para buscar
        temporizadorDebounce = setTimeout(() => {
            // Consulta AJAX al servidor
            fetch(`/intranet/pacientes/buscar/?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest' // Le decimos a Django que es AJAX
                }
            })
                .then(response => response.json())
                .then(data => {
                    // Si se encuentra mascota, se construye la tabla
                    if (data.resultados.length > 0) {
                        let html = `
                        <h5 class="text-muted mb-3">Resultados para: "${data.query}"</h5>
                        <div class="table-responsive bg-white shadow-sm rounded">
                            <table class="table table-hover align-middle mb-0">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Paciente</th>
                                        <th>Especie / Edad</th>
                                        <th>Dueño</th>
                                        <th>RUT Dueño</th>
                                        <th class="text-center">Acción</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;

                        data.resultados.forEach(m => {
                            // Construir URL de manera dinámica
                            const urlHistorial = `/intranet/pacientes/${m.id_mascota}/historial/`;

                            html += `
                            <tr>
                                <td><strong>${m.nombre}</strong></td>
                                <td>${m.especie} (${m.edad})</td>
                                <td>${m.dueno_nombre}</td>
                                <td><span class="badge bg-secondary">${m.dueno_rut}</span></td>
                                <td class="text-center">
                                    <a href="${urlHistorial}" class="btn btn-success btn-sm fw-bold">
                                        Ver Historial Médico
                                    </a>
                                </td>
                            </tr>
                        `;
                        });

                        html += `</tbody></table></div>`;
                        contenedorResultados.innerHTML = html;
                    } else {
                        // Si no hay resultados
                        contenedorResultados.innerHTML = `
                        <h5 class="text-muted mb-3">Resultados para: "${data.query}"</h5>
                        <div class="alert alert-warning text-center py-4">
                            <h5 class="mb-0">No se encontraron pacientes que coincidan con su búsqueda.</h5>
                        </div>
                    `;
                    }
                })
                .catch(error => {
                    console.error('Error al realizar la búsqueda:', error);
                    contenedorResultados.innerHTML = `<div class="alert alert-danger text-center">Ocurrió un error en el servidor. Intente nuevamente.</div>`;
                });

        }, 300); // 300ms de retraso
    });
});