document.addEventListener('DOMContentLoaded', function () {
    // 1. VALIDACIÓN DEL FORMULARIO DE CARGOS
    const formCargo = document.getElementById('form-cargo');
    if (formCargo) {
        formCargo.addEventListener('submit', function (e) {
            const inputDesc = document.getElementById('input-desc-cargo');

            // Evitar envíos vacíos o solo con espacios
            if (inputDesc.value.trim() === '') {
                e.preventDefault();
                inputDesc.classList.add('is-invalid');
                return;
            } else {
                inputDesc.classList.remove('is-invalid');
            }

            // Prevenir doble clic
            const btn = document.getElementById('btn-cargo');
            btn.disabled = true;
            btn.innerHTML = 'Procesando ...';
        });

        // Quitar color rojo apenas el usuario empiece a corregir
        document.getElementById('input-desc-cargo').addEventListener('input', function () {
            this.classList.remove('is-invalid');
        });
    }

    // 2. VALIDACIÓN DEL FORMULARIO DE SERVICIOS
    const formServicio = document.getElementById('form-servicio');
    if (formServicio) {
        formServicio.addEventListener('submit', function (e) {
            const inputDesc = document.getElementById('input-desc-servicio');
            const inputMonto = document.getElementById('input-monto');
            const inputDuracion = document.getElementById('input-duracion');

            let isValid = true;

            // Validar texto vacío (Descripción)
            if (inputDesc.value.trim() === '') {
                inputDesc.classList.add('is-invalid');
                document.getElementById('feedback-desc-servicio').style.display = 'block';
                isValid = false;
            } else {
                inputDesc.classList.remove('is-invalid');
                document.getElementById('feedback-desc-servicio').style.display = 'none';
            }

            // Validar monto (Bloqueo estricto por debajo de 7990)
            const montoValue = parseInt(inputMonto.value);
            const montoMinimo = 7990;

            if (isNaN(montoValue) || montoValue < montoMinimo) {
                inputMonto.classList.add('is-invalid');
                document.getElementById('feedback-monto').textContent = `El valor mínimo permitido es de $${montoMinimo} CLP.`;
                document.getElementById('feedback-monto').classList.remove('d-none');
                isValid = false;
            } else {
                inputMonto.classList.remove('is-invalid');
                document.getElementById('feedback-monto').classList.add('d-none');
            }

            // Validar duración (debe ser al menos 15 minutos)
            if (inputDuracion.value === '' || parseInt(inputDuracion.value) < 15) {
                inputDuracion.classList.add('is-invalid');
                document.getElementById('feedback-duracion').classList.remove('d-none');
                isValid = false;
            } else {
                inputDuracion.classList.remove('is-invalid');
                document.getElementById('feedback-duracion').classList.add('d-none');
            }

            // Si hay errores, detener el envío
            if (!isValid) {
                e.preventDefault();
                return;
            }

            // Prevenir doble clic solo si todo está bien
            const btn = document.getElementById('btn-servicio');
            btn.disabled = true;
            btn.innerHTML = 'Procesando...';
        });

        // Limpiar estilos de error al teclear
        ['input-desc-servicio', 'input-monto', 'input-duracion'].forEach(id => {
            document.getElementById(id).addEventListener('input', function () {
                this.classList.remove('is-invalid');
                if (id === 'input-desc-servicio') {
                    document.getElementById('feedback-desc-servicio').style.display = 'none';
                }
                if (id === 'input-monto') {
                    document.getElementById('feedback-monto').classList.add('d-none');
                }
            });
        });
    }

    // FORMATEO DE MONTOS EN LA INTERFAZ (Ej: 25000 -> 25.000)
    // Busca todos los elementos con la clase 'monto-formatear'
    document.querySelectorAll('.monto-formatear').forEach(function (elemento) {
        // Obtener el número puro
        let valor = parseInt(elemento.textContent);
        if (!isNaN(valor)) {
            elemento.textContent = new Intl.NumberFormat('es-CL').format(valor);
        }
    });
});