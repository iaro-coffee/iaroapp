
var ctx1 = document.getElementById("chart-line1").getContext("2d");
var ctx2 = document.getElementById("chart-line2").getContext("2d");
var ctx3 = document.getElementById("chart-line3").getContext("2d");

var gradientStroke1 = ctx1.createLinearGradient(0, 230, 0, 50);
gradientStroke1.addColorStop(1, 'rgba(203,12,159,0.2)');
gradientStroke1.addColorStop(0.2, 'rgba(72,72,176,0.0)');
gradientStroke1.addColorStop(0, 'rgba(203,12,159,0)'); //purple colors

var gradientStroke2 = ctx2.createLinearGradient(0, 230, 0, 50);
gradientStroke2.addColorStop(1, 'rgba(87,95,154,0.2)');
gradientStroke2.addColorStop(0.2, 'rgba(108,112,154,0.0)');
gradientStroke2.addColorStop(0, 'rgba(133,135,154,0)'); //blue colors

var gradientStroke3 = ctx3.createLinearGradient(0, 230, 0, 50);
gradientStroke3.addColorStop(1, 'rgba(255,136,0,0.2)');
gradientStroke3.addColorStop(0.2, 'rgba(255,193,121,0.0)');
gradientStroke3.addColorStop(0, 'rgba(255,221,182,0)'); //orange colors

new Chart(ctx1, {
    type: "line",
    data: {
        labels: statistics['labels'],
        datasets: [{
            label: "Work hours",
            tension: 0.4,
            borderWidth: 0,
            pointRadius: 0,
            borderColor: "#cb0c9f",
            borderWidth: 3,
            backgroundColor: gradientStroke1,
            fill: true,
            data: statistics['workHours'],
            maxBarThickness: 6
        },
        ],
    },
    options: {
        spanGaps: true,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            }
        },
        interaction: {
            intersect: false,
            mode: 'index',
        },
        scales: {
            y: {
                grid: {
                    drawBorder: false,
                    display: true,
                    drawOnChartArea: true,
                    drawTicks: false,
                    borderDash: [5, 5]
                },
                ticks: {
                    display: true,
                    padding: 10,
                    color: '#b2b9bf',
                    font: {
                        size: 11,
                        family: "Open Sans",
                        style: 'normal',
                        lineHeight: 2
                    },
                }
            },
            x: {
                grid: {
                    drawBorder: false,
                    display: false,
                    drawOnChartArea: false,
                    drawTicks: false,
                    borderDash: [5, 5]
                },
                ticks: {
                    display: true,
                    color: '#b2b9bf',
                    padding: 20,
                    font: {
                        size: 11,
                        family: "Open Sans",
                        style: 'normal',
                        lineHeight: 2
                    },
                }
            },
        },
    },
});
new Chart(ctx2, {
    type: "line",
    data: {
        labels: statistics['labels'],
        datasets: [
            {
                label: "Tasks",
                tension: 0.4,
                borderWidth: 0,
                pointRadius: 0,
                borderColor: "#575f9a",
                borderWidth: 3,
                backgroundColor: gradientStroke2,
                fill: true,
                data: statistics['tasks'],
                maxBarThickness: 6
            },
        ],
    },
    options: {
        spanGaps: true,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            }
        },
        interaction: {
            intersect: false,
            mode: 'index',
        },
        scales: {
            y: {
                grid: {
                    drawBorder: false,
                    display: true,
                    drawOnChartArea: true,
                    drawTicks: false,
                    borderDash: [5, 5]
                },
                ticks: {
                    display: true,
                    padding: 10,
                    color: '#b2b9bf',
                    font: {
                        size: 11,
                        family: "Open Sans",
                        style: 'normal',
                        lineHeight: 2
                    },
                }
            },
            x: {
                grid: {
                    drawBorder: false,
                    display: false,
                    drawOnChartArea: false,
                    drawTicks: false,
                    borderDash: [5, 5]
                },
                ticks: {
                    display: true,
                    color: '#b2b9bf',
                    padding: 20,
                    font: {
                        size: 11,
                        family: "Open Sans",
                        style: 'normal',
                        lineHeight: 2
                    },
                }
            },
        },
    },
});
new Chart(ctx3, {
    type: "line",
    data: {
        labels: statistics['labels'],
        datasets: [
            {
                label: "Rating",
                tension: 0.4,
                borderWidth: 0,
                pointRadius: 0,
                borderColor: "orange",
                borderWidth: 3,
                backgroundColor: gradientStroke3,
                fill: true,
                data: statistics['ratings'],
                maxBarThickness: 6
            },
        ],
    },
    options: {
        spanGaps: true,
        responsive: true,
        maintainAspectRatio: false,
        min: 1,
        max: 5,
        plugins: {
            legend: {
                display: false,
            }
        },
        interaction: {
            intersect: false,
            mode: 'index',
        },
        scales: {
            y: {
                grid: {
                    drawBorder: false,
                    display: true,
                    drawOnChartArea: true,
                    drawTicks: false,
                    borderDash: [5, 5]
                },
                ticks: {
                    display: true,
                    padding: 10,
                    color: '#b2b9bf',
                    font: {
                        size: 11,
                        family: "Open Sans",
                        style: 'normal',
                        lineHeight: 2
                    },
                }
            },
            x: {
                grid: {
                    drawBorder: false,
                    display: false,
                    drawOnChartArea: false,
                    drawTicks: false,
                    borderDash: [5, 5]
                },
                ticks: {
                    display: true,
                    color: '#b2b9bf',
                    padding: 20,
                    font: {
                        size: 11,
                        family: "Open Sans",
                        style: 'normal',
                        lineHeight: 2
                    },
                }
            },
        },
    },
});
