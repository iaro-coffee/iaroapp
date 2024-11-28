document.addEventListener("DOMContentLoaded", function () {
    const treeElement = document.getElementById("tree");
    const isSuperuser = treeElement.getAttribute("data-is-superuser") === "true";
    console.log(isSuperuser);
    // Department Template
    OrgChart.templates.departmentTemplate = Object.assign({}, OrgChart.templates.ana);

    // Customize rectangle and font styles for departments
    OrgChart.templates.departmentTemplate.node = `
        <rect x="0" y="0" height="120" width="250" rx="10" ry="10" fill="#ffffff"></rect>
    `;
    OrgChart.templates.departmentTemplate.img_0 = `
        <circle cx="50" cy="60" r="40" fill="none" stroke="#000000" stroke-width="1"></circle>
        <defs>
            <clipPath id="circleClipDepartment">
                <circle cx="50" cy="60" r="40"></circle>
            </clipPath>
        </defs>
        <image xlink:href="{val}" x="10" y="20" height="80" width="80" clip-path="url(#circleClipDepartment)" preserveAspectRatio="xMidYMid slice"></image>
    `;
    OrgChart.templates.departmentTemplate.field_0 = `
        <text text-anchor="end" style="font-size: 18px; fill: #000000;" x="240" y="40">
            {val}
        </text>
    `;
    OrgChart.templates.departmentTemplate.field_1 = `
        <text text-anchor="end" style="font-size: 16px; fill: #000000;" x="240" y="70">
            {val}
        </text>
    `;

    // Shareholder Template
    OrgChart.templates.shareholderTemplate = Object.assign({}, OrgChart.templates.ana);

    OrgChart.templates.shareholderTemplate.node = `
        <rect x="0" y="0" height="120" width="250" rx="10" ry="10" fill="#000000"></rect>
    `;
    OrgChart.templates.shareholderTemplate.img_0 = `
        <circle cx="50" cy="60" r="40" fill="none" stroke="#000000" stroke-width="1"></circle>
        <defs>
            <clipPath id="circleClipShareholder">
                <circle cx="50" cy="60" r="40"></circle>
            </clipPath>
        </defs>
        <image xlink:href="{val}" x="10" y="20" height="80" width="80" clip-path="url(#circleClipShareholder)" preserveAspectRatio="xMidYMid slice"></image>
    `;
    OrgChart.templates.shareholderTemplate.field_0 = `
        <text text-anchor="end" style="font-size: 18px; fill: #ffffff;" x="240" y="40">
            {val}
        </text>
    `;
    OrgChart.templates.shareholderTemplate.field_1 = `
        <text text-anchor="end" style="font-size: 16px; fill: #ffffff;" x="240" y="70">
            {val}
        </text>
    `;

    // Default Node Template
    OrgChart.templates.defaultNodeTemplate = Object.assign({}, OrgChart.templates.ana);

    OrgChart.templates.defaultNodeTemplate.node = `
        <rect x="0" y="0" height="120" width="250" rx="10" ry="10" fill="#d8ead0"></rect>
    `;
    OrgChart.templates.defaultNodeTemplate.img_0 = `
        <circle cx="50" cy="60" r="40" fill="none" stroke="#000000" stroke-width="1"></circle>
        <defs>
            <clipPath id="circleClipDefault">
                <circle cx="50" cy="60" r="40"></circle>
            </clipPath>
        </defs>
        <image xlink:href="{val}" x="10" y="20" height="80" width="80" clip-path="url(#circleClipDefault)" preserveAspectRatio="xMidYMid slice"></image>
    `;

    OrgChart.templates.defaultNodeTemplate.field_0 = `
        <text text-anchor="end" style="font-size: 18px; fill: #000000;" x="240" y="40">
            {val}
        </text>
    `;
    OrgChart.templates.defaultNodeTemplate.field_1 = `
        <text text-anchor="end" style="font-size: 16px; fill: #000000;" x="240" y="70">
            {val}
        </text>
    `;


    OrgChart.templates.itTemplate = Object.assign({}, OrgChart.templates.ana);
    OrgChart.templates.itTemplate.nodeMenuButton = "";
    OrgChart.templates.itTemplate.nodeCircleMenuButton = {
        radius: 18,
        x: 250,
        y: 60,
        color: "#fff",
        stroke: "#f10707",
    };

    // Initialize the chart
    const chart = new OrgChart(document.getElementById("tree"), {
        mouseScrool: OrgChart.action.ctrlZoom,
        scaleInitial: 1,
        enableSearch: false,
        enableDragDrop: isSuperuser,
        assistantSeparation: 170,
        template: "defaultNodeTemplate",
        toolbar: {
            fullScreen: true,
            zoom: true,
            fit: true,
            // expandAll: true,
        },
        nodeBinding: {
            field_0: "name",
            field_1: "title",
            img_0: "img",
        },
        nodeMenu: isSuperuser
            ? {
                details: { text: "Details" },
                edit: { text: "Edit Node" },
                add: { text: "Add Node" },
                remove: { text: "Remove Node" },
                addShareholder: {
                    text: "Add Shareholder",
                    icon: OrgChart.icon.add(24, 24, "#039BE5"),
                    onClick: function (nodeId) {
                        const node = chart.getNode(nodeId);
                        const newId = OrgChart.randomId();
                        const shareholderName = prompt("Enter Shareholder Name:");
                        if (shareholderName) {
                            chart.addNode({
                                id: newId,
                                pid: null,
                                name: shareholderName,
                                title: "Shareholder",
                                tags: ["shareholder"],
                            });
                        }
                    },
                },
                addDepartment: {
                    text: "Add Department",
                    icon: OrgChart.icon.add(24, 24, "#039BE5"),
                    onClick: function (nodeId) {
                        const newId = OrgChart.randomId();
                        const departmentName = prompt("Enter Department Name:");
                        if (departmentName) {
                            chart.addNode({
                                id: newId,
                                pid: nodeId,
                                name: departmentName,
                                title: "Department",
                                tags: ["department"],
                            });
                        }
                    },
                },
            }
            : null, // Hide node menu for non-superusers
        tags: {
            root: {
                template: "group",
                subTreeConfig: {
                    layout: OrgChart.treeBottom,
                },
            },
            shareholder: {
                template: "shareholderTemplate",
                subTreeConfig: {
                    layout: OrgChart.treeRightOffset,
                },
                nodeBinding: {
                    field_1: "title",
                },
            },
            department: {
                template: "departmentTemplate",
                subTreeConfig: {
                    layout: OrgChart.mixed,
                },
                nodeBinding: {
                    field_1: "title",
                },
            },
        },
    });

    // Load initial data from API
    fetch("/api/org-chart/")
        .then((response) => response.json())
        .then((data) => {
            if (Array.isArray(data) && data.length > 0) {
                chart.load(data);
            } else {
                chart.load([
                    {
                        id: "root",
                        name: "Company",
                        title: "Root Node",
                        img: "https://cdn.balkan.app/shared/anim/1.gif",
                        tags: ["root"],
                    },
                ]);
            }
        })
        .catch((error) => console.error("Error loading chart data:", error));

    // Save chart data
    document.getElementById("saveChartBtn").addEventListener("click", () => {
        const chartData = chart.config.nodes || [];
        if (!Array.isArray(chartData) || chartData.length === 0) {
            alert("No valid chart data to save!");
            return;
        }

        fetch("/api/org-chart/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(chartData),
        })
            .then((response) => {
                if (response.ok) {
                    alert("Changes saved successfully!");
                } else {
                    console.error("Error saving chart:", response.statusText);
                }
            })
            .catch((error) => console.error("Error saving chart:", error));
    });

    chart.on("add", (sender, args) => {
        console.log("Node added:", args);
    });

    chart.on("remove", (sender, args) => {
        console.log("Node removed:", args);
    });
});
