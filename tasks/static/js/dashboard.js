/* globals Chart:false, feather:false */

(() => {
  'use strict'
  // Graphs
  const ctx = document.getElementById('tipsChart')
  // eslint-disable-next-line no-unused-vars
  const myChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [
        'Sunday',
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday'
      ],
      datasets: [{
        data: [
          15339,
          21345,
          18483,
          24003,
          23489,
          24092,
          12034
        ],
      }]
    },
    options: {
      plugins: {
        legend: {
            display: false
        },
      },
      scales: {
        yAxes: [{
          ticks: {
            beginAtZero: false
          }
        }]
      },
    }
  })
})()
