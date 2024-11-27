document.addEventListener('DOMContentLoaded', function () {
    const chart = new OrgChart(document.getElementById("tree"), {
        mouseScrool: OrgChart.action.ctrlZoom,
        scaleInitial: 1,
        scaleMin: 0.5,
        scaleMax: 2,
        enableDragDrop: true,
        enableSearch: false,
        template: "ana",
        nodeBinding: {
            field_0: "name",
            field_1: "title",
            img_0: "img"
        },
        nodeMenu: {
            details: { text: "Details" },
            edit: { text: "Edit" },
            add: { text: "Add Node" },
            remove: { text: "Remove Node" },
            addDepartment: {
                text: "Add Department",
                icon: OrgChart.icon.add(24, 24, '#039BE5'),
                onClick: function (nodeId) {
                    const newId = OrgChart.randomId();
                    const departmentName = prompt("Enter the department name:");
                    if (departmentName) {
                        chart.addNode({
                            id: newId,
                            pid: nodeId,
                            name: departmentName,
                            title: "Department",
                            tags: ["department"]
                        });
                        console.log(`Department added: ${departmentName}`);
                    }
                }
            }
        },
        tags: {
            "department": {
                template: "group",
                subTreeConfig: {
                    orientation: OrgChart.orientation.bottom
                }
            }
        }
    });

    // Load initial data from API
    fetch('/api/org-chart/')
        .then(response => response.json())
        .then(data => {
            if (Array.isArray(data) && data.length > 0) {
                chart.load(data);
            } else {
                console.warn("No valid chart data found. Initializing with default node.");
                chart.load([{ id: 1, name: "Root Node", title: "CEO" }]);
            }
        })
        .catch(error => console.error("Error loading chart data:", error));

    // Save chart data to API
    document.getElementById("saveChartBtn").addEventListener("click", () => {
        const chartData = chart.config.nodes || [];
        if (!Array.isArray(chartData) || chartData.length === 0) {
            alert("No valid chart data to save!");
            console.error("No valid data from chart.get()");
            return;
        }

        fetch('/api/org-chart/', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(chartData)
        })
        .then(response => {
            if (response.ok) {
                alert("Changes saved successfully!");
                console.log("Chart saved successfully");
            } else {
                console.error("Error saving chart:", response.statusText);
            }
        })
        .catch(error => console.error("Error saving chart:", error));
    });

    // Example: Adding event listeners for chart updates
    chart.on("update", (sender, args) => {
        console.log("Node updated:", args);
    });

    chart.on("add", (sender, args) => {
        console.log("Node added:", args);
    });

    chart.on("remove", (sender, args) => {
        console.log("Node removed:", args);
    });
});
