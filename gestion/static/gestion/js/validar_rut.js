document.addEventListener('DOMContentLoaded', function () {
    const inputRut = document.getElementById('input-rut');
    const feedbackRut = document.getElementById('rut-feedback');

    // Verificar que el input exista antes de intentar buscar el form
    if (inputRut) {
        const formProfesional = inputRut.closest('form');

        // Función para limpiar y dar formato al RUT
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

        // Función JS para validar Módulo 11 en el frontend
        function validarRut(rutCompleto) {
            if (!/^[0-9]+[-|‐]{1}[0-9kK]{1}$/.test(rutCompleto.replace(/\./g, ''))) return false;
            let tmp = rutCompleto.replace(/\./g, '').split('-');
            let digv = tmp[1].toUpperCase();
            let rut = tmp[0];
            if (digv == 'K') digv = 10;
            if (digv == '0') digv = 11;
            let suma = 0;
            let multiplo = 2;
            for (let i = rut.length - 1; i >= 0; i--) {
                suma = suma + rut.charAt(i) * multiplo;
                if (multiplo < 7) multiplo++;
                else multiplo = 2;
            }
            let res = 11 - (suma % 11);
            return res == digv;
        }

        // Evento que se dispara cada vez que el usuario escribe una letra
        inputRut.addEventListener('input', function (e) {
            // Formatear en vivo
            let rutFormateado = formatearRut(this.value.toUpperCase().replace(/[^0-9K]/g, ''));
            this.value = rutFormateado;

            // Validar y cambiar colores
            if (rutFormateado.length >= 9) {
                if (validarRut(rutFormateado)) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    if (feedbackRut) feedbackRut.classList.add('d-none');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                    if (feedbackRut) feedbackRut.classList.remove('d-none');
                }
            } else {
                this.classList.remove('is-valid', 'is-invalid');
                if (feedbackRut) feedbackRut.classList.add('d-none');
            }
        });

        // Evitar que el formulario se envíe si el RUT es inválido
        if (formProfesional) {
            formProfesional.addEventListener('submit', function (e) {
                if (inputRut.classList.contains('is-invalid')) {
                    e.preventDefault(); // Detiene el envío
                    inputRut.focus();
                }
            });
        }
    }
});