document.addEventListener('DOMContentLoaded', function () {
    // Busca todos los elementos con la clase 'monto-formatear' y les pone formato chileno
    document.querySelectorAll('.monto-formatear').forEach(function (elemento) {
        let valor = parseInt(elemento.textContent);
        if (!isNaN(valor)) {
            elemento.textContent = new Intl.NumberFormat('es-CL').format(valor);
        }
    });
});