// Define the nodes and links for the Sankey diagram
var nodes = ["Education", "Data Analysis", "Machine Learning", "Data Visualization", "Projects"];
var links = [
    {"source": 0, "target": 1, "value": 4},  // Education to Data Analysis
    {"source": 1, "target": 2, "value": 3},  // Data Analysis to Machine Learning
    {"source": 2, "target": 3, "value": 3},  // Machine Learning to Data Visualization
    {"source": 3, "target": 4, "value": 5}   // Data Visualization to Projects
];

// Create the Sankey diagram
var data = {
    type: "sankey",
    node: {
        pad: 15,
        thickness: 20,
        line: {
            color: "black",
            width: 0.5
        }
    },
    link: {
        source: links.map(link => link.source),
        target: links.map(link => link.target),
        value: links.map(link => link.value)
    }
};

var layout = {
    // title: "Data Science Journey - Sankey Diagram"
};

Plotly.newPlot("sankey-diagram", [data], layout);