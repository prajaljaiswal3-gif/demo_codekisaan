/**
 * CodeKisaan Farm Visual Analytics with Chart.js
 * Visualizes Crop Health Distribution and Agro-Climatic Risk Trends
 */

function renderDashboardCharts(cropStats, weatherData) {
    // 1. Crop Health Doughnut Chart
    const healthCtx = document.getElementById("cropHealthChart");
    if (healthCtx) {
        new Chart(healthCtx, {
            type: "doughnut",
            data: {
                labels: ["निरोगी / Healthy (72%)", "बुरशी / Fungal Blight (18%)", "कीड / Sucking Pest (10%)"],
                datasets: [{
                    data: [72, 18, 10],
                    backgroundColor: ["#2d6a4f", "#e76f51", "#e9c46a"],
                    hoverBackgroundColor: ["#1b4332", "#c44536", "#d4a373"],
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
                            boxWidth: 14,
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: "#0f2d1e",
                        titleFont: { family: "'Outfit', sans-serif", size: 13 },
                        bodyFont: { family: "'Plus Jakarta Sans', sans-serif", size: 12 }
                    }
                },
                cutout: "68%"
            }
        });
    }

    // 2. Weekly Weather & Fungal Risk Trend
    const riskCtx = document.getElementById("weatherTrendChart");
    if (riskCtx) {
        const days = ["सोम (Mon)", "मंगळ (Tue)", "बुध (Wed)", "गुरू (Thu)", "शुक्र (Fri)", "शनि (Sat)", "रवि (Sun)"];
        new Chart(riskCtx, {
            type: "line",
            data: {
                labels: days,
                datasets: [
                    {
                        label: "आर्द्रता / Humidity (%)",
                        data: [58, 62, 70, 78, 74, 65, 60],
                        borderColor: "#3a86ff",
                        backgroundColor: "rgba(58, 134, 255, 0.08)",
                        fill: true,
                        tension: 0.35,
                        yAxisID: "y"
                    },
                    {
                        label: "तापमान / Temp (°C)",
                        data: [29, 30, 28, 27, 28, 31, 32],
                        borderColor: "#e76f51",
                        borderDash: [4, 4],
                        fill: false,
                        tension: 0.35,
                        yAxisID: "y1"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: {
                        position: "top",
                        labels: { font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 }, boxWidth: 12 }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 } }
                    },
                    y: {
                        type: "linear",
                        display: true,
                        position: "left",
                        title: { display: true, text: "आर्द्रता (%)", font: { size: 11 } },
                        min: 30,
                        max: 100
                    },
                    y1: {
                        type: "linear",
                        display: true,
                        position: "right",
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: "तापमान (°C)", font: { size: 11 } },
                        min: 15,
                        max: 42
                    }
                }
            }
        });
    }
}
