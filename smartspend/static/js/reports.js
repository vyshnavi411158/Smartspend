
const expenseCanvas = document.getElementById("expenseChart");

if (expenseCanvas) {

    const months = monthlyChart.map(item => item[2]);

    const expenses = monthlyChart.map(item => Number(item[3]));

    new Chart(expenseCanvas, {

        type: "bar",

        data: {

            labels: months,

            datasets: [{

                label: "Expenses",

                data: expenses,

                backgroundColor: "#6366F1",

                borderRadius: 8

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    display: false

                }

            },

            scales: {

                y: {

                    beginAtZero: true

                }

            }

        }

    });

}




const categoryCanvas = document.getElementById("categoryChart");

if (categoryCanvas) {

    const categories = categoryChart.map(item => item[0]);

    const totals = categoryChart.map(item => Number(item[1]));

    new Chart(categoryCanvas, {

        type: "doughnut",

        data: {

            labels: categories,

            datasets: [{

                data: totals,

                backgroundColor: [

                    "#6366F1",

                    "#06B6D4",

                    "#22C55E",

                    "#F59E0B",

                    "#EF4444",

                    "#8B5CF6",

                    "#14B8A6",

                    "#F97316",

                    "#EC4899"

                ]

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    position: "bottom"

                }

            }

        }

    });

}




const trendCanvas = document.getElementById("trendChart");

if (trendCanvas) {

    const months = monthlyChart.map(item => item[2]);

    const expenses = monthlyChart.map(item => Number(item[3]));

    new Chart(trendCanvas, {

        type: "line",

        data: {

            labels: months,

            datasets: [{

                label: "Expense Trend",

                data: expenses,

                borderColor: "#22C55E",

                backgroundColor: "rgba(34,197,94,0.15)",

                fill: true,

                tension: 0.4

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false

        }

    });

}