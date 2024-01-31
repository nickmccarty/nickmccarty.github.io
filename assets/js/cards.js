document.addEventListener('DOMContentLoaded', function () {
    // Card Animation Script
    var cards = document.querySelectorAll('.card');

    function fadeInUpCards() {
        cards.forEach(function (card, index) {
            setTimeout(function () {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 600); // Adjust the delay between cards
        });
    }

    // Trigger card animation
    setTimeout(fadeInUpCards, 1000);
});