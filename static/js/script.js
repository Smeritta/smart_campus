function showAlert() {
    const alertBox = document.getElementById("alertBox");

    if (alertBox) {
        alertBox.style.display = "flex";
    }
}

function closeAlert() {
    const alertBox = document.getElementById("alertBox");

    if (alertBox) {
        alertBox.style.display = "none";
    }
}
