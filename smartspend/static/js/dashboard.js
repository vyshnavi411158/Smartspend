

const expenseCanvas = document.getElementById("expenseChart");

if (expenseCanvas) {

    const monthlyLabels = monthlyChart.map(item => item[2]);
    const monthlyValues = monthlyChart.map(item => Number(item[3]));

    new Chart(expenseCanvas, {

        type: "bar",

        data: {

            labels: monthlyLabels,

            datasets: [{

                label: "Monthly Expenses",

                data: monthlyValues,

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