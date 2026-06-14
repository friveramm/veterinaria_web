document.addEventListener('DOMContentLoaded', function () {
    // Busca todos los elementos con la clase 'monto-formatear' y les pone formato chileno
    document.querySelectorAll('.monto-formatear').forEach(function (elemento) {
        let valor = parseInt(elemento.textContent);
        if (!isNaN(valor)) {
            elemento.textContent = new Intl.NumberFormat('es-CL').format(valor);
        }
    });

    // Referencias a las etiquetas <img> del carrusel
    const img1 = document.getElementById('img-slide-1');
    const img2 = document.getElementById('img-slide-2');
    const img3 = document.getElementById('img-slide-3');

    // 1. Buscar un Gato (Cat API)
    fetch('https://api.thecatapi.com/v1/images/search')
        .then(res => res.json())
        .then(data => {
            img1.src = data[0].url;
        })
        .catch(err => console.error('Error carga gato:', err));

    // 2. Buscar un Perro (Dog CEO API)
    fetch('https://dog.ceo/api/breeds/image/random')
        .then(res => res.json())
        .then(data => {
            img2.src = data.message;
        })
        .catch(err => console.error('Error carga perro:', err));

    // 3. Buscar otro Gato (Cat API)
    fetch('https://api.thecatapi.com/v1/images/search')
        .then(res => res.json())
        .then(data => {
            img3.src = data[0].url;
        })
        .catch(err => console.error('Error carga gato 2:', err));
});