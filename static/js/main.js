/* ===========================
   SEARCH FILTER
=========================== */

function filterBySearch() {
    let input = document.getElementById("searchInput").value.toLowerCase();
    let rows = document.querySelectorAll("table tbody tr");

    rows.forEach(row => {
        let text = row.innerText.toLowerCase();
        row.style.display = text.includes(input) ? "" : "none";
    });
}

/* ===========================
   SCORE FILTER
=========================== */

function filterByScore() {
    let filter = document.getElementById("scoreFilter").value;
    let rows = document.querySelectorAll("table tbody tr");

    rows.forEach(row => {
        let progressBar = row.querySelector(".progress-bar");
        if (!progressBar) return;

        let score = parseFloat(progressBar.dataset.score);

        if (filter === "all") {
            row.style.display = "";
        }
        else if (filter === "80" && score >= 80) {
            row.style.display = "";
        }
        else if (filter === "60" && score >= 60 && score < 80) {
            row.style.display = "";
        }
        else if (filter === "low" && score < 60) {
            row.style.display = "";
        }
        else {
            row.style.display = "none";
        }
    });
}

/* ===========================
   PAGE LOAD ANIMATION
=========================== */

document.addEventListener("DOMContentLoaded", function() {
    document.body.classList.add("fade-in");
});