document.addEventListener('DOMContentLoaded', function () {
    const textarea = document.getElementById('ficha-descripcion');
    const btnActualizar = document.getElementById('btn-actualizar');
    const contador = document.getElementById('contador-caracteres');

    if (textarea && contador) {
        // Función para actualizar el contador visualmente
        const actualizarContador = () => {
            const longitudActual = textarea.value.length;
            contador.textContent = `${longitudActual} / 3000 caracteres`;

            // Alerta visual opcional si se está acercando al límite (ej: 2800 caracteres)
            if (longitudActual >= 2800) {
                contador.classList.replace('text-muted', 'text-danger');
            } else {
                contador.classList.replace('text-danger', 'text-muted');
            }
        };

        // Ejecutar el conteo inicial con los datos que vengan de la BD
        const valorInicial = textarea.value;
        actualizarContador();

        // Escuchar la escritura del usuario
        textarea.addEventListener('input', function () {
            // 1. Ejecutar el contador dinámico
            actualizarContador();

            // 2. Controlar la activación del botón de actualización (si existe en pantalla)
            if (btnActualizar) {
                if (textarea.value === valorInicial) {
                    btnActualizar.disabled = true;
                } else {
                    btnActualizar.disabled = false;
                }
            }
        });
    }
});