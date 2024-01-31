var text = "Python Machine Learning Data Analysis SQL TensorFlow Pandas";

// Create an array of words
var words = text.split(" ");

// Create a word frequency object
var wordFrequency = {};
words.forEach(function(word) {
    wordFrequency[word] = (wordFrequency[word] || 0) + 1;
});

// Convert the word frequency object to an array of objects
var wordCloudData = Object.keys(wordFrequency).map(function(word) {
    return { text: word, size: wordFrequency[word] };
});

// Set up D3 word cloud layout
var layout = d3.layout.cloud()
    .size([400, 200])
    .words(wordCloudData)
    .padding(5)
    .rotate(function() { return ~~(Math.random() * 2) * 90; })
    .font("Impact")
    .fontSize(function(d) { return d.size * 10; })
    .on("end", draw);

// Generate the word cloud
layout.start();

// Draw the word cloud
function draw(words) {
    d3.select("#word-cloud").append("svg")
        .attr("width", layout.size()[0])
        .attr("height", layout.size()[1])
        .append("g")
        .attr("transform", "translate(" + layout.size()[0] / 2 + "," + layout.size()[1] / 2 + ")")
        .selectAll("text")
        .data(words)
        .enter().append("text")
        .style("font-size", function(d) { return d.size + "px"; })
        .style("font-family", "Impact")
        .style("fill", "black")
        .attr("text-anchor", "middle")
        .attr("transform", function(d) {
            return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
        })
        .text(function(d) { return d.text; });
}
