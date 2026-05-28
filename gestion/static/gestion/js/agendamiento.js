const sucursalSelect = document.getElementById('selector-sucursal');
const servicioSelect = document.getElementById('selector-servicio');
const profesionalSelect = document.getElementById('selector-profesional');

// Caso 1: Cambia la Sucursal -> Poblar Servicios
sucursalSelect.addEventListener('change', function () {
    const sucursalId = this.value;

    // Limpieza total de cascada hacia abajo
    servicioSelect.innerHTML = '<option value="">Primero selecciona una sucursal...</option>';
    servicioSelect.disabled = true;
    profesionalSelect.innerHTML = '<option value="">Primero selecciona un servicio...</option>';
    profesionalSelect.disabled = true;

    if (!sucursalId) return;

    // Consumir API de servicios
    fetch(`/api/servicios/?sucursal_id=${sucursalId}`)
        .then(response => response.json())
        .then(data => {
            servicioSelect.innerHTML = '<option value="">-- Seleccionar Servicio --</option>';
            if (data.servicios && data.servicios.length > 0) {
                data.servicios.forEach(s => {
                    const option = document.createElement('option');
                    option.value = s.id;
                    option.textContent = `${s.descripcion} (${s.monto} ${s.divisa})`;
                    servicioSelect.appendChild(option);
                });
                servicioSelect.disabled = false;
            } else {
                servicioSelect.innerHTML = '<option value="">No hay servicios disponibles en esta sucursal</option>';
            }
        })
        .catch(error => console.error('Error al cargar servicios:', error));
});

// Caso 2: Cambia el Servicio -> Poblar Profesionales Filtrados por la Sucursal elegida
servicioSelect.addEventListener('change', function () {
    const servicioId = this.value;
    const sucursalId = sucursalSelect.value;

    profesionalSelect.innerHTML = '<option value="">Primero selecciona un servicio...</option>';
    profesionalSelect.disabled = true;

    if (!servicioId || !sucursalId) return;

    // Consumir la API de profesionales enviando ambos parámetros
    fetch(`/api/profesionales/?servicio_id=${servicioId}&sucursal_id=${sucursalId}`)
        .then(response => response.json())
        .then(data => {
            profesionalSelect.innerHTML = '<option value="">-- Seleccionar Profesional --</option>';
            if (data.profesionales && data.profesionales.length > 0) {
                data.profesionales.forEach(p => {
                    const option = document.createElement('option');
                    option.value = p.id;
                    option.textContent = `${p.nombre} (${p.cargo})`;
                    profesionalSelect.appendChild(option);
                });
                profesionalSelect.disabled = false;
            } else {
                profesionalSelect.innerHTML = '<option value="">No hay profesionales disponibles para este procedimiento en esta sucursal</option>';
            }
        })
        .catch(error => console.error('Error al cargar profesionales:', error));
});