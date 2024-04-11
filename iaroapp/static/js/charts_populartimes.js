// Chart time
const now = new Date();
const hours = [];
for (let i = 7; i <= 17; i++) {
    const suffix = i < 12 ? 'AM' : 'PM';
    const hourIn12 = i > 12 ? i - 12 : i;
    hours.push(`${hourIn12} ${suffix}`);
}
// Current time
const currentTime = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
console.log('Current time:', currentTime); // Debugging


// Mapping JS day index to popularTime data structure
const currentHour = new Date().getHours();
const jsDayOfWeek  = new Date().getDay(); // JS day, 0-Sunday, 1-Monday, ..., 6-Saturday
const dayIndex = jsDayOfWeek === 0 ? 6 : jsDayOfWeek - 1; // API day, 0-Monday, ..., 6-Sunday
console.log('dayIndex:', dayIndex); // Debugging
const todayData = populartimesData[dayIndex];
console.log('todayData:', todayData); // Debugging

const currentPopularityIndex = currentHour; // Assuming index 0 corresponds to midnight
const nextPopularityIndex = currentPopularityIndex + 1;
console.log('Current hour index:', currentPopularityIndex, ' Next  hour index:', nextPopularityIndex); // Debugging

const currentUsualPopularity = todayData.data[currentPopularityIndex];
console.log('current hour: ', currentHour); // Debugging
console.log('Current usual popularity:', currentUsualPopularity); // Debugging

const nextHourPopularity = todayData.data[nextPopularityIndex];
console.log('Current Live popularity:', currentLivePopularity); // Debugging
console.log('Next hour popularity:', nextHourPopularity); // Debugging

let currentLiveStatus = getLiveStatus(currentLivePopularity, currentUsualPopularity); // Pass the usual popularity for comparison
let nextStatus = getLiveStatus(nextHourPopularity, nextHourPopularity);
console.log('Current Live status:', currentLiveStatus); // Debugging
console.log('Next hour status:', nextStatus); // Debugging



const ctx = document.getElementById('populartimesChart').getContext('2d');
const gradient = ctx.createLinearGradient(0, 0, 0, 150);
gradient.addColorStop(0, 'rgba(203,12,159)');
gradient.addColorStop(1, 'rgba(87,95,154)');

const livePopularityData = new Array(hours.length).fill(null); // Use null for empty values
const currentHourIndex = currentHour - 7;
console.log('Current hour index:', currentHourIndex); // Debugging
// Only set the live popularity for the current hour
if (currentHour >= 7 && currentHour <= 17) {
    // Calculate the index for the current hour based on your hours array
    // Ensure livePopularity is a number and assign it to the correct position
    livePopularityData[currentHourIndex] = Number(livePopularity);
}


// Generate datasets for each day with hidden state except for the first one
// Initialize datasets once
const datasets = populartimesData.map((day, index) => ({
    label: day.name,
    data: day.data.slice(7, 17),
    backgroundColor: gradient,
    borderRadius: 10,
    hidden: true, // Initially hide all
    barThickness: 9,
}));


// Add live popularity dataset
datasets.push({
    id: 'livePopularity',
    label: 'Current Live Popularity',
    data: livePopularityData,
    backgroundColor: 'rgba(130,214,22,0.65)',
    borderRadius: 10,
    barThickness: 9,
    borderColor: 'green',
    borderWidth: 0,
    order: 1,
    hidden: true,
});


// Function to update the active day styling in the legend
function updateLegendActiveStyle(activeIndex) {
    const legendItems = document.querySelectorAll('.legend-item');
    legendItems.forEach((item, index) => {
        if (index === activeIndex) {
            if (index !== new Date().getDay() - 1) {
                item.style.color = 'rgba(203,12,159,1)';
            }
        } else {
            item.style.color = '#344767'; // Default color
        }
    });
    legendItems[new Date().getDay() - 1].style.color = '#82d616'; // Always green for the current day
}



// Function to update the chart for a specific day
function updateChartForDay(dayIndex) {
    // Hide all datasets
    datasets.forEach((dataset, index) => {
        dataset.hidden = index !== dayIndex;
    });

    // Check if the live popularity should be shown
    const liveIndex = datasets.findIndex(d => d.id === 'livePopularity');
    datasets[liveIndex].hidden = dayIndex !== (new Date().getDay() - 1);

    // Update the chart
    populartimesChart.update();

    // Update legend style
    updateLegendActiveStyle(dayIndex);
}



// Prediction logic
function updatePredictions() {
    let predictionText = `Day is winding down!`;

    if (typeof nextHourPopularity !== 'undefined') {
        if (nextHourPopularity > currentLivePopularity) {
            predictionText = `${currentLiveStatus}. Expecting more people in the next hour.`;
        } else if (nextHourPopularity < currentLivePopularity) {
            predictionText = `${currentLiveStatus}. Expecting fewer people in the next hour.`;
        }
    }

    const liveInfoElement = document.querySelector('.predict__info');
    if (liveInfoElement) {
        liveInfoElement.innerHTML = `<b>Live: ${currentTime} </b> ${predictionText}`;
    } else {
        console.error('Live info element not found in the DOM');
    }
}

// Live status logic
function getLiveStatus(currentLivePopularity, usualPopularity) {
    if (currentLivePopularity === usualPopularity) {
        return 'As busy as usual';
    } else if (currentLivePopularity > usualPopularity) {
        const ratio = currentLivePopularity / usualPopularity;
        if (ratio >= 2) {
            return 'Much more busy than usual';
        } else if (ratio >= 1.5) {
            return 'More busy than usual';
        } else {
            return 'Slightly busier than usual';
        }
    } else {
        const ratio = usualPopularity / currentLivePopularity;
        if (ratio >= 2) {
            return 'Much less busy than usual';
        } else if (ratio >= 1.5) {
            return 'Less busy than usual';
        } else {
            return 'Slightly less busy than usual';
        }
    }
}

// Usual Status logic
function getUsualStatus(value) {
    if (value >= 80) {
        return 'As busy as it gets';
    } else if (value >= 60) {
        return 'Quite busy';
    } else if (value >= 40) {
        return 'A little busy';
    } else if (value >= 20) {
        return 'Not too busy';
    } else if (value > 0) {
        return 'Not busy';
    } else {
        return 'Closed';
    }
}



let populartimesChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: hours,
        datasets: datasets,
        tension: 0.4,
        pointRadius: 0,
        borderColor: "#cb0c9f",
        borderWidth: 0,
        fill: true,
        maxBarThickness: 6
    },
    options: {
        onHover: (event, chartElement) => {
            const target = event.native ? event.native.target : event.target;
            if (chartElement.length > 0) {
                target.style.cursor = 'pointer';
            } else {
                target.style.cursor = 'default';
            }
        },
        spanGaps: true,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            tooltip: {
                enabled: true,
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: function(context) {
                        if (context.dataset.id === 'livePopularity' && context.dataIndex === currentHourIndex) {
                            return `Live: ${context.raw}% (${currentLiveStatus})`;
                        } else if (context.dataset.id !== 'livePopularity') {
                            const usualStatus = getUsualStatus(context.raw);
                            return `${context.dataset.label}: ${context.raw}% (${usualStatus})`;
                        }
                        return null;
                    }
                }
            },
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
                    autoSkip: true,
                    maxTicksLimit: 5,
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
                    maxTicksLimit: 5,
                    color: '#b2b9bf',
                    padding: 20,
                    maxRotation: 0,
                    minRotation: 0,
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




// Custom chart legend
const legendContainer = document.getElementById('chartLegend');

// Initialize the chart and legend
populartimesData.forEach((day, index) => {
    const legendItem = document.createElement('h6');
    legendItem.textContent = day.name.slice(0, 2);
    legendItem.className = 'legend-item mx-1';
    legendItem.style.cursor = 'pointer';
    legendItem.onclick = () => {
        updateChartForDay(index);
    };

    legendContainer.appendChild(legendItem);
});

populartimesData.forEach((data) => {
    console.log(data.name);
});
console.log('Today\'s place:', todayData.name);


// Init document
document.addEventListener('DOMContentLoaded', function() {
    updatePredictions();

    // Init chart on today and update legend styling
    const todayIndex = new Date().getDay() - 1;
    updateChartForDay(todayIndex);
    updateLegendActiveStyle(todayIndex);
});




// Future updates
// Summaries
const daySummaries = populartimesData.map(day => {
    return {
        day: day.name,
        total: day.data.reduce((acc, val) => acc + val, 0)
    };
});
const sortedDays = daySummaries.sort((a, b) => a.total - b.total);
sortedDays.forEach(daySummary => {
    //console.log(`${daySummary.day}: ${daySummary.total}`);
});




