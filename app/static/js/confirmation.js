// Confirmation avant d'envoyer un formulaire portant l'attribut
// data-confirmation (suppressions, désactivations...)
document.addEventListener("submit", function (evenement) {
    const message = evenement.target.dataset.confirmation;
    if (message && !window.confirm(message)) {
        evenement.preventDefault();
    }
});
