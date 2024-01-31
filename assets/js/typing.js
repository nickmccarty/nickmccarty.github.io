document.addEventListener('DOMContentLoaded', function () {
    // Words to be typed
    var words = ["Web Developer", "Data Scientist", "ML/AI Engineer"];

    var index = 0;
    var wordIndex = 0;
    var currentWord = "";
    var isDeleting = false;

    function type() {
        var speed = isDeleting ? 50 : 100; // Adjust the speed as needed

        if (index === words.length) {
            index = 0;
        }

        currentWord = words[index];

        document.getElementById('typed-text').textContent = currentWord.slice(0, wordIndex);

        if (isDeleting) {
            wordIndex--;
        } else {
            wordIndex++;
        }

        if (!isDeleting && wordIndex === currentWord.length + 1) {
            isDeleting = true;
            speed = 800; // pause before deleting
        } else if (isDeleting && wordIndex === 0) {
            isDeleting = false;
            index++;
            speed = 200; // pause before typing next word
        }

        setTimeout(type, speed);
    }

    type(); // Start typing animation
});

