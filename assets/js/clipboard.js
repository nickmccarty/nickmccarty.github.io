document.addEventListener('DOMContentLoaded', function () {
    // Initialize Clipboard.js
    var clipboard = new ClipboardJS('#copyButton');

    // On success
    clipboard.on('success', function (e) {
        e.clearSelection();

        // Show tooltip
        var tooltip = new bootstrap.Tooltip(document.getElementById('copyButton'), {
            title: 'Copied 🙌🏽',
            placement: 'right',
            trigger: 'manual'
        });

        tooltip.show();

        // Hide tooltip after a short delay (e.g., 2 seconds)
        setTimeout(function () {
            tooltip.hide();
        }, 2000);
    });

    // On error
    clipboard.on('error', function (e) {
        console.error('Failed to copy code.');
    });

    // Update highlight.js when the content changes
    clipboard.on('success', function (e) {
        hljs.highlightBlock(e.trigger.nextElementSibling);
    });
});