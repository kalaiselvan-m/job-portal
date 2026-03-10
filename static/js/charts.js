document.addEventListener("DOMContentLoaded", function () {

    const chartCanvas = document.getElementById("statusChart");
    if (!chartCanvas) return;

    const shortlisted = parseInt(chartCanvas.dataset.shortlisted || 0);
    const rejected = parseInt(chartCanvas.dataset.rejected || 0);

    const ctx = chartCanvas.getContext("2d");

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Shortlisted', 'Rejected'],
            datasets: [{
                data: [shortlisted, rejected],
                backgroundColor: ['#28a745', '#dc3545'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,   // 🔥 Important Fix
            cutout: '65%',                // 🔥 Controls donut thickness
            animation: {
                animateScale: true,
                animateRotate: true
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

});