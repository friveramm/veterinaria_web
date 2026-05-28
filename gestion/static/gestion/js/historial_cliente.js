document.addEventListener('DOMContentLoaded', function () {
    const botonesCalificar = document.querySelectorAll('.btn-calificar');
    const inputCitaId = document.getElementById('modal-cita-id');
    const spanMascotaNombre = document.getElementById('modal-mascota-nombre');

    // Contador y limpieza
    const textarea = document.getElementById('floatingTextarea');
    const contador = document.getElementById('contador-palabras');
    const radioStars = document.querySelectorAll('.rating-stars input');
    const btnSubmit = document.querySelector('#modalFeedback button[type="submit"]');

    // 1. Lógica al abrir el Modal
    botonesCalificar.forEach(boton => {
        boton.addEventListener('click', function () {
            const citaId = this.getAttribute('data-cita-id');
            const mascotaNombre = this.getAttribute('data-mascota-nombre');

            // Inyectar datos en el formulario oculto
            inputCitaId.value = citaId;
            spanMascotaNombre.textContent = mascotaNombre;

            // UX: Limpiar el formulario y el contador para que esté en blanco al abrir
            if (textarea) textarea.value = '';
            if (contador) {
                contador.textContent = '0 palabras (Máx. 50)';
                contador.classList.remove('text-danger', 'fw-bold');
                contador.classList.add('text-muted');
            }
            if (btnSubmit) btnSubmit.disabled = false;

            // Desmarcar las estrellas
            radioStars.forEach(radio => radio.checked = false);
        });
    });

    // 2. Contador de Palabras en tiempo real
    if (textarea && contador) {
        textarea.addEventListener('input', function () {
            // Obtener el texto, quitar espacios al inicio/fin
            let texto = this.value.trim();

            // Contar palabras dividiendo por espacios (si está vacío es 0)
            let palabras = texto === '' ? 0 : texto.split(/\s+/).length;

            contador.textContent = `${palabras} palabra${palabras === 1 ? '' : 's'} (Máx. 50)`;

            // UX: Límite visual y bloqueo
            if (palabras > 50) {
                contador.classList.remove('text-muted');
                contador.classList.add('text-danger', 'fw-bold');
                if (btnSubmit) btnSubmit.disabled = true; // Bloquea el envío
            } else {
                contador.classList.remove('text-danger', 'fw-bold');
                contador.classList.add('text-muted');
                if (btnSubmit) btnSubmit.disabled = false; // Permite el envío
            }
        });
    }
});