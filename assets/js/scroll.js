$(document).ready(function () {
    $(".owl-carousel").owlCarousel({
        loop: true,
        margin: 30,
        nav: false,
        autoplay: true,
        dots: false,
        autoplayTimeout: 2000, // Adjust the timeout between slides
        responsive: {
            0: {
                items: 3 // Adjust the number of logos visible on smaller screens
            },
            600: {
                items: 5
            },
            1000: {
                items: 7
            }
        }
    });
});