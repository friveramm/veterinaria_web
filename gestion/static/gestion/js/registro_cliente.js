document.addEventListener('DOMContentLoaded', function () {
    // 0. LÓGICA DE ÉXITO: CONTADOR Y REDIRECCIÓN
    const contadorEl = document.getElementById('contador');
    if (contadorEl) {
        let segundos = 10;
        // Obtener la URL que inyectó Django en el HTML
        const urlLogin = contadorEl.getAttribute('data-url-login');

        const intervalo = setInterval(function () {
            segundos--;
            contadorEl.textContent = segundos;

            if (segundos <= 0) {
                clearInterval(intervalo);
                if (urlLogin) {
                    window.location.href = urlLogin; // Redirección usando la variable
                }
            }
        }, 1000); // 1000 milisegundos
    }

    // LÓGICA DEL FORMULARIO DE REGISTRO
    const formRegistro = document.getElementById('form-registro');
    const urlValidacion = formRegistro ? formRegistro.getAttribute('data-url-validacion') : '';

    // 1. USERNAME: AJAX + FORMATO (Sin espacios)
    const inputUsername = document.getElementById('input-username');
    const feedbackUsername = document.getElementById('username-feedback');
    let timeoutUsername;

    if (inputUsername) {
        inputUsername.addEventListener('input', function () {
            this.value = this.value.toLowerCase().replace(/\s+/g, '');
            clearTimeout(timeoutUsername);

            if (this.value.length >= 4 && urlValidacion) {
                timeoutUsername = setTimeout(() => {
                    fetch(`${urlValidacion}?username=${this.value}`)
                        .then(r => r.json())
                        .then(data => {
                            if (data.username_usado) {
                                this.classList.remove('is-valid');
                                this.classList.add('is-invalid');
                                this.setAttribute('data-error-api', 'true');
                                if (feedbackUsername) {
                                    feedbackUsername.textContent = 'Este usuario ya está en uso. Elige otro.';
                                    feedbackUsername.classList.remove('d-none');
                                }
                            } else {
                                this.removeAttribute('data-error-api');
                                this.classList.remove('is-invalid');
                                this.classList.add('is-valid');
                                if (feedbackUsername) feedbackUsername.classList.add('d-none');
                            }
                        });
                }, 500);
            } else {
                this.classList.remove('is-valid', 'is-invalid');
                if (feedbackUsername) feedbackUsername.classList.add('d-none');
            }
        });
    }

    // 2. RUT: AJAX (La validación matemática la hace validar_rut.js)
    const inputRut = document.getElementById('input-rut');
    const feedbackRut = document.getElementById('rut-feedback');
    let timeoutRut;

    if (inputRut && urlValidacion) {
        inputRut.addEventListener('input', function () {
            clearTimeout(timeoutRut);
            if (this.value.length >= 8) {
                timeoutRut = setTimeout(() => {
                    fetch(`${urlValidacion}?rut=${this.value}`)
                        .then(r => r.json())
                        .then(data => {
                            if (data.rut_usado) {
                                this.classList.remove('is-valid');
                                this.classList.add('is-invalid');
                                this.setAttribute('data-error-api', 'true');
                                if (feedbackRut) {
                                    feedbackRut.textContent = 'Este RUT ya tiene una cuenta registrada.';
                                    feedbackRut.classList.remove('d-none');
                                }
                            } else {
                                this.removeAttribute('data-error-api');
                                if (feedbackRut) feedbackRut.textContent = 'RUT inválido.';
                            }
                        });
                }, 500);
            }
        });
    }

    // 3. CORREO: REGEX + AJAX
    const inputEmail = document.getElementById('input-email');
    const feedbackEmail = document.getElementById('email-feedback');
    let timeoutEmail;

    if (inputEmail) {
        inputEmail.addEventListener('input', function () {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            clearTimeout(timeoutEmail);

            if (this.value.trim().length > 0) {
                if (emailRegex.test(this.value)) {
                    // Si el formato es correcto, verificar en BD
                    if (urlValidacion) {
                        timeoutEmail = setTimeout(() => {
                            fetch(`${urlValidacion}?email=${this.value}`)
                                .then(r => r.json())
                                .then(data => {
                                    if (data.email_usado) {
                                        inputEmail.classList.remove('is-valid');
                                        inputEmail.classList.add('is-invalid');
                                        inputEmail.setAttribute('data-error-api', 'true');
                                        if (feedbackEmail) {
                                            feedbackEmail.textContent = 'Este correo ya está registrado.';
                                            feedbackEmail.classList.remove('d-none');
                                        }
                                    } else {
                                        inputEmail.removeAttribute('data-error-api');
                                        inputEmail.classList.remove('is-invalid');
                                        inputEmail.classList.add('is-valid');
                                        if (feedbackEmail) feedbackEmail.classList.add('d-none');
                                    }
                                });
                        }, 500);
                    }
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                    if (feedbackEmail) {
                        feedbackEmail.textContent = 'Ingresa un correo válido (ej: nombre@correo.com).';
                        feedbackEmail.classList.remove('d-none');
                    }
                }
            } else {
                this.classList.remove('is-valid', 'is-invalid');
                if (feedbackEmail) feedbackEmail.classList.add('d-none');
            }
        });
    }

    // 4. TELÉFONO
    const inputFonoVisible = document.getElementById('input-fono-visible');
    const inputFonoOculto = document.getElementById('input-fono-oculto');
    const feedbackFono = document.getElementById('fono-feedback');

    if (inputFonoVisible) {
        inputFonoVisible.addEventListener('input', function () {
            // Eliminar cualquier cosa que no sea un dígito numérico
            this.value = this.value.replace(/\D/g, '');

            // Validar que tenga exactamente la longitud de un celular chileno (8 dígitos)
            if (this.value.length === 8) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
                if (feedbackFono) feedbackFono.classList.add('d-none');

                // Unir el +569 con los 8 dígitos y se inyecta al input oculto que viaja a Django
                if (inputFonoOculto) {
                    inputFonoOculto.value = '+569' + this.value;
                }
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
                if (feedbackFono) feedbackFono.classList.remove('d-none');

                // Si está incompleto, vaciamos el input oculto para que no se envíe basura
                if (inputFonoOculto) {
                    inputFonoOculto.value = '';
                }
            }
        });
    }

    // 5. PROTECCIÓN GENERAL DE OBLIGATORIOS (BORDES ROJOS)
    if (formRegistro) {
        const requiredInputs = formRegistro.querySelectorAll('[required]');

        requiredInputs.forEach(input => {
            input.addEventListener('input', function () {
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

        // 6. BLOQUEO FINAL ANTES DEL ENVÍO
        formRegistro.addEventListener('submit', function (e) {
            let tieneErrores = false;

            const nameInputs = ['primer_nombre', 'primer_apellido'];
            nameInputs.forEach(name => {
                const el = document.querySelector(`input[name="${name}"]`);
                if (el && el.value.trim() === '') {
                    el.classList.add('is-invalid');
                    tieneErrores = true;
                }
            });

            const inputsAPI = [inputUsername, inputRut, inputEmail];
            inputsAPI.forEach(el => {
                if (el && (el.classList.contains('is-invalid') || el.hasAttribute('data-error-api'))) {
                    el.focus();
                    tieneErrores = true;
                }
            });

            if (tieneErrores) {
                e.preventDefault();
                return;
            }

            const btnGuardar = document.getElementById('btn-registrar');
            if (btnGuardar) {
                btnGuardar.disabled = true;
                btnGuardar.innerHTML = 'Creando cuenta...';
            }
        });
    }
});