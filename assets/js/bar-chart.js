// Create a sample data array
var data = [{
    x: ['Data Analysis', 'Machine Learning', 'Data Visualization'],
    y: [3, 4, 2],
    type: 'bar',
    text: ['3 years', '4 years', '2 years']
}];

// Create an interactive bar chart using Plotly.js
Plotly.newPlot('bar-chart', data);
