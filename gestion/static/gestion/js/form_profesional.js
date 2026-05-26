document.addEventListener('DOMContentLoaded', function () {

    // 1. FILTRO DE USERNAME
    const inputUsername = document.getElementById('input-username');
    if (inputUsername) {
        inputUsername.addEventListener('input', function () {
            this.value = this.value.toLowerCase().replace(/\s+/g, '');
        });
    }

    // 2. VALIDACIÓN DE CORREO
    const inputEmail = document.getElementById('input-email');
    const feedbackEmail = document.getElementById('email-feedback');
    if (inputEmail) {
        inputEmail.addEventListener('input', function () {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (this.value.length > 0) {
                if (emailRegex.test(this.value)) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    if (feedbackEmail) feedbackEmail.classList.add('d-none');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                    if (feedbackEmail) feedbackEmail.classList.remove('d-none');
                }
            } else {
                this.classList.remove('is-valid', 'is-invalid');
                if (feedbackEmail) feedbackEmail.classList.add('d-none');
            }
        });
    }

    // 3. LÓGICA DINÁMICA DE CARGOS Y ESPECIALIDADES
    const selectCargo = document.getElementById('select-cargo');
    const seccionEspecialidades = document.getElementById('seccion-especialidades');
    const checkboxes = document.querySelectorAll('.check-servicio');

    function alternarEspecialidades() {
        if (!selectCargo || !seccionEspecialidades) return;

        // Se obntiene el texto del cargo que está seleccionado actualmente (en minúsculas)
        const cargoSeleccionado = selectCargo.options[selectCargo.selectedIndex].text.toLowerCase();

        // Si el cargo es administrativo, ocultamos la caja y limpiamos los checks
        if (cargoSeleccionado.includes('recepcionista') || cargoSeleccionado.includes('administrador')) {
            seccionEspecialidades.style.display = 'none';
            checkboxes.forEach(chk => chk.checked = false);
        } else {
            // Si es un perfil médico, volvemos a mostrar la caja
            seccionEspecialidades.style.display = 'block';
        }
    }

    if (selectCargo) {
        // Escuchar cada vez que el usuario cambia la opción
        selectCargo.addEventListener('change', alternarEspecialidades);
        // Ejecutar inmediatamente al cargar la página por si ya venía seleccionado un recepcionista
        alternarEspecialidades();
    }

    // 4. VALIDACIÓN DEL FORMULARIO Y PROTECCIÓN DE DOBLE CLICK
    const formMaestro = document.getElementById('form-maestro');
    if (formMaestro) {
        formMaestro.addEventListener('submit', function (e) {

            // A. Validar checkboxes solo si la sección está visible (si es un rol médico)
            if (seccionEspecialidades && seccionEspecialidades.style.display !== 'none') {
                const errorServicios = document.getElementById('error-servicios');
                let alMenosUnoMarcado = false;

                checkboxes.forEach(function (chk) {
                    if (chk.checked) alMenosUnoMarcado = true;
                });

                if (!alMenosUnoMarcado && checkboxes.length > 0) {
                    e.preventDefault();
                    errorServicios.classList.remove('d-none');
                    const cajaServicios = document.getElementById('caja-servicios');
                    cajaServicios.classList.add('border-danger');
                    return;
                } else {
                    errorServicios.classList.add('d-none');
                    document.getElementById('caja-servicios').classList.remove('border-danger');
                }
            }

            // B. Revisar si el RUT es válido
            const inputRut = document.getElementById('input-rut');
            if (inputRut && inputRut.classList.contains('is-invalid')) {
                e.preventDefault();
                inputRut.focus();
                return;
            }

            // C. Revisar si el Correo es válido
            if (inputEmail && inputEmail.classList.contains('is-invalid')) {
                e.preventDefault();
                inputEmail.focus();
                return;
            }

            // D. Prevenir Doble Click
            const btnGuardar = document.getElementById('btn-guardar-maestro');
            if (btnGuardar) {
                btnGuardar.disabled = true;
                btnGuardar.innerHTML = 'Procesando y guardando...';
            }
        });
    }
});