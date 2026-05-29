document.addEventListener('DOMContentLoaded', function () {

    const formMaestro = document.getElementById('form-maestro');
    const urlValidacion = formMaestro ? formMaestro.getAttribute('data-url-validacion') : '';
    const profId = formMaestro ? formMaestro.getAttribute('data-prof-id') : '';

    // 1. FILTRO Y VALIDACIÓN ASÍNCRONA DE USERNAME EN TIEMPO REAL (AJAX)
    const inputUsername = document.getElementById('input-username');
    const feedbackUsername = document.getElementById('username-feedback');
    let timeoutUsername;

    if (inputUsername) {
        inputUsername.addEventListener('input', function () {
            this.value = this.value.toLowerCase().replace(/\s+/g, '');
            clearTimeout(timeoutUsername);

            // Solo consultar si tiene al menos 3 caracteres
            if (this.value.length > 2 && urlValidacion) {
                timeoutUsername = setTimeout(() => {
                    fetch(`${urlValidacion}?username=${this.value}`)
                        .then(r => r.json())
                        .then(data => {
                            if (data.username_usado) {
                                this.classList.remove('is-valid');
                                this.classList.add('is-invalid');
                                this.setAttribute('data-error-api', 'true');
                                if (feedbackUsername) {
                                    feedbackUsername.textContent = 'Este usuario ya está en uso en el sistema.';
                                    feedbackUsername.classList.remove('d-none');
                                }
                            } else {
                                this.removeAttribute('data-error-api');
                                this.classList.remove('is-invalid');
                                this.classList.add('is-valid');
                                if (feedbackUsername) feedbackUsername.classList.add('d-none');
                            }
                        });
                }, 500); // 500ms de retraso para no saturar BD
            } else if (this.value.length === 0) {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
                if (feedbackUsername) feedbackUsername.classList.add('d-none');
            }
        });
    }

    // 2. VALIDACIÓN ASÍNCRONA DE RUT EN TIEMPO REAL (AJAX)
    const inputRut = document.getElementById('input-rut');
    const feedbackRut = document.getElementById('rut-feedback');
    let timeoutRut;

    if (inputRut && urlValidacion) {
        inputRut.addEventListener('input', function () {
            clearTimeout(timeoutRut);

            if (this.value.length >= 8) {
                timeoutRut = setTimeout(() => {
                    fetch(`${urlValidacion}?rut=${this.value}&exclude_id=${profId}`)
                        .then(r => r.json())
                        .then(data => {
                            if (data.rut_usado) {
                                this.classList.remove('is-valid');
                                this.classList.add('is-invalid');
                                this.setAttribute('data-error-api', 'true');
                                if (feedbackRut) {
                                    feedbackRut.textContent = `Error: RUT ya registrado a nombre de ${data.rut_dueno}`;
                                    feedbackRut.classList.remove('d-none');
                                }
                            } else {
                                this.removeAttribute('data-error-api');
                                // Si no está duplicado, restauramos el mensaje original por si falla la matemática
                                if (feedbackRut) feedbackRut.textContent = 'RUT inválido.';
                            }
                        });
                }, 500);
            }
        });
    }

    // 3. VALIDACIÓN DE CORREO EN TIEMPO REAL
    const inputEmail = document.getElementById('input-email');
    const feedbackEmail = document.getElementById('email-feedback');
    if (inputEmail) {
        function validarEmailReactivo() {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (inputEmail.value.trim().length > 0) {
                if (emailRegex.test(inputEmail.value)) {
                    inputEmail.classList.remove('is-invalid');
                    inputEmail.classList.add('is-valid');
                    if (feedbackEmail) feedbackEmail.classList.add('d-none');
                } else {
                    inputEmail.classList.remove('is-valid');
                    inputEmail.classList.add('is-invalid');
                    if (feedbackEmail) feedbackEmail.classList.remove('d-none');
                }
            } else {
                inputEmail.classList.remove('is-valid');
                inputEmail.classList.add('is-invalid');
                if (feedbackEmail) feedbackEmail.classList.add('d-none');
            }
        }
        inputEmail.addEventListener('input', validarEmailReactivo);
        inputEmail.addEventListener('blur', validarEmailReactivo);
    }

    // 4. PROTECCIÓN Y LÍMITE DE CARACTERES EN LOS NOMBRES
    const inputPrimerNombre = document.querySelector('input[name="primer_nombre"]');
    const inputSegundoNombre = document.querySelector('input[name="segundo_nombre"]');
    const inputPrimerApellido = document.querySelector('input[name="primer_apellido"]');
    const inputSegundoApellido = document.querySelector('input[name="segundo_apellido"]');

    const nameInputs = [inputPrimerNombre, inputSegundoNombre, inputPrimerApellido, inputSegundoApellido];

    nameInputs.forEach(input => {
        if (input) {
            input.addEventListener('input', function () {
                if (this.value.length > 24) {
                    this.value = this.value.slice(0, 24);
                }
            });
        }
    });

    // 5. COMPORTAMIENTO GENERAL DE CAMPOS OBLIGATORIOS
    if (formMaestro) {
        const requiredInputs = formMaestro.querySelectorAll('[required]');
        requiredInputs.forEach(input => {
            input.addEventListener('input', function () {
                // Excluimos los campos que tienen validaciones especiales y asíncronas
                if (this.type !== 'email' && this.id !== 'input-username' && this.id !== 'input-rut') {
                    if (this.value.trim().length === 0) {
                        this.classList.add('is-invalid');
                    } else {
                        this.classList.remove('is-invalid');
                    }
                }
            });

            input.addEventListener('blur', function () {
                if (this.type !== 'email' && this.id !== 'input-username' && this.id !== 'input-rut') {
                    if (this.value.trim().length === 0) {
                        this.classList.add('is-invalid');
                    }
                }
            });

            input.addEventListener('invalid', function () {
                this.classList.add('is-invalid');
            });
        });
    }

    // 6. LÓGICA DINÁMICA DE CARGOS Y ESPECIALIDADES
    const selectCargo = document.getElementById('select-cargo');
    const seccionEspecialidades = document.getElementById('seccion-especialidades');
    const checkboxes = document.querySelectorAll('.check-servicio');

    function alternarEspecialidades() {
        if (!selectCargo || !seccionEspecialidades) return;
        const cargoSeleccionado = selectCargo.options[selectCargo.selectedIndex].text.toLowerCase();
        if (cargoSeleccionado.includes('recepcionista') || cargoSeleccionado.includes('administrador')) {
            seccionEspecialidades.style.display = 'none';
            checkboxes.forEach(chk => chk.checked = false);
        } else {
            seccionEspecialidades.style.display = 'block';
        }
    }

    if (selectCargo) {
        selectCargo.addEventListener('change', alternarEspecialidades);
        alternarEspecialidades();
    }

    // 7. BLOQUEO FINAL ANTES DEL ENVÍO
    if (formMaestro) {
        formMaestro.addEventListener('submit', function (e) {
            let tieneErrores = false;

            if (inputPrimerNombre && inputPrimerNombre.value.trim() === '') {
                inputPrimerNombre.classList.add('is-invalid');
                tieneErrores = true;
            }

            if (inputPrimerApellido && inputPrimerApellido.value.trim() === '') {
                inputPrimerApellido.classList.add('is-invalid');
                tieneErrores = true;
            }

            if (seccionEspecialidades && seccionEspecialidades.style.display !== 'none') {
                const errorServicios = document.getElementById('error-servicios');
                let alMenosUnoMarcado = false;
                checkboxes.forEach(chk => { if (chk.checked) alMenosUnoMarcado = true; });

                if (!alMenosUnoMarcado && checkboxes.length > 0) {
                    errorServicios.classList.remove('d-none');
                    document.getElementById('caja-servicios').classList.add('border-danger');
                    tieneErrores = true;
                } else {
                    errorServicios.classList.add('d-none');
                    document.getElementById('caja-servicios').classList.remove('border-danger');
                }
            }

            if (inputRut && (inputRut.classList.contains('is-invalid') || inputRut.hasAttribute('data-error-api'))) {
                inputRut.focus();
                tieneErrores = true;
            }

            if (inputUsername && (inputUsername.classList.contains('is-invalid') || inputUsername.hasAttribute('data-error-api'))) {
                inputUsername.focus();
                tieneErrores = true;
            }

            if (inputEmail && inputEmail.classList.contains('is-invalid')) {
                inputEmail.focus();
                tieneErrores = true;
            }

            if (tieneErrores) {
                e.preventDefault();
                return;
            }

            const btnGuardar = document.getElementById('btn-guardar-maestro');
            if (btnGuardar) {
                btnGuardar.disabled = true;
                btnGuardar.innerHTML = 'Procesando y guardando...';
            }
        });
    }
});