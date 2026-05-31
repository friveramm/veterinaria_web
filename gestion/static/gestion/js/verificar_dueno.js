document.addEventListener('DOMContentLoaded', function () {

    const inputRut = document.getElementById('input-rut');
    const feedbackDueno = document.getElementById('dueno-feedback');
    const listaResultados = document.getElementById('lista-resultados-dueno');

    const urlBuscar = inputRut ? inputRut.getAttribute('data-url-buscar') : '';
    let timeoutBuscador;

    // Flag para evitar el bucle infinito
    let seleccionDesdeLista = false;

    // Limpiar y dar formato visual al RUT
    function formatearRut(rut) {
        let actual = rut.replace(/^0+/, "");
        if (actual != '' && actual.length > 1) {
            let sinPuntos = actual.replace(/\./g, "");
            let actualLimpio = sinPuntos.replace(/-/g, "");
            let inicio = actualLimpio.substring(0, actualLimpio.length - 1);
            let rutPuntos = "";
            let i = 0;
            let j = 1;
            for (i = inicio.length - 1; i >= 0; i--) {
                let letra = inicio.charAt(i);
                rutPuntos = letra + rutPuntos;
                if (j % 3 == 0 && j <= inicio.length - 1) {
                    rutPuntos = "." + rutPuntos;
                }
                j++;
            }
            let dv = actualLimpio.substring(actualLimpio.length - 1);
            return rutPuntos + "-" + dv;
        }
        return rut;
    }

    if (inputRut && urlBuscar) {
        inputRut.addEventListener('input', function () {

            // Si el evento input se disparó por hacer clic en la lista, aborta
            if (seleccionDesdeLista) {
                seleccionDesdeLista = false;
                return;
            }

            clearTimeout(timeoutBuscador);

            // 1. Aplicar el formato al input inmediatamente
            let rutFormateado = formatearRut(this.value.toUpperCase().replace(/[^0-9K]/g, ''));
            this.value = rutFormateado;

            // 2. Extraer solo los números para la búsqueda limpia en backend
            const valorActual = rutFormateado.replace(/[^0-9K]/g, '');

            // Si ha digitado al menos 3 caracteres, empezar a buscar
            if (valorActual.length >= 3) {
                timeoutBuscador = setTimeout(() => {
                    fetch(`${urlBuscar}?rut=${valorActual}`)
                        .then(r => r.json())
                        .then(data => {
                            listaResultados.innerHTML = ''; // Limpiar resultados viejos

                            if (data.resultados.length > 0) {
                                // Mostrar el menú flotante y limpiar errores visuales
                                listaResultados.classList.remove('d-none');
                                inputRut.classList.remove('is-invalid');

                                data.resultados.forEach(dueno => {
                                    const li = document.createElement('li');
                                    li.className = 'list-group-item list-group-item-action text-primary';

                                    // Formatear el RUT que viene de la Base de Datos
                                    let rutBdFormateado = formatearRut(dueno.rut_bd.toUpperCase());

                                    li.innerHTML = `<strong>${rutBdFormateado}</strong> - ${dueno.nombre}`;

                                    li.addEventListener('click', function () {
                                        seleccionDesdeLista = true;

                                        // Pegar el RUT ya formateado en el input
                                        inputRut.value = rutBdFormateado;

                                        // Esconder la lista permanentemente
                                        listaResultados.classList.add('d-none');

                                        // Mensaje de éxito y borde verde
                                        inputRut.classList.remove('is-invalid');
                                        inputRut.classList.add('is-valid');
                                        feedbackDueno.innerHTML = `<span class="text-success fw-bold fs-6">Dueño asociado: ${dueno.nombre}</span>`;
                                    });

                                    listaResultados.appendChild(li);
                                });
                            } else {
                                // Si no hay coincidencias
                                listaResultados.classList.add('d-none');
                                inputRut.classList.remove('is-valid');

                                // Evaluar la longitud para saber si le avisamos de un error definitivo o si sigue escribiendo
                                if (valorActual.length >= 8) {
                                    inputRut.classList.add('is-invalid');
                                    feedbackDueno.innerHTML = `<span class="text-danger fw-bold">El cliente NO está registrado. Debe crear su cuenta primero.</span>`;
                                } else {
                                    inputRut.classList.remove('is-invalid');
                                    feedbackDueno.innerHTML = `<span class="text-muted">No se encontraron clientes...</span>`;
                                }
                            }
                        }).catch(err => console.error('Error:', err));
                }, 300);
            } else {
                listaResultados.classList.add('d-none');
                listaResultados.innerHTML = '';
                inputRut.classList.remove('is-invalid', 'is-valid');
                feedbackDueno.innerHTML = 'Teclea el RUT para buscar al cliente en nuestra base de datos.';
            }
        });

        // Ocultar lista al hacer clic afuera
        document.addEventListener('click', function (event) {
            if (event.target !== inputRut && event.target !== listaResultados) {
                if (listaResultados) listaResultados.classList.add('d-none');
            }
        });
    }
});