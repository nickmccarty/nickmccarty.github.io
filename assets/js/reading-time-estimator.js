// Get the article text
const articleText = document.getElementById('article').innerText;

// Split the text into an array of words
const wordsArray = articleText.split(' ');

// Count the number of words in the array
const wordCount = wordsArray.length;

// Calculate the estimated reading time
const wordsPerMinute = 175;
const readingTime = Math.ceil(wordCount / wordsPerMinute);

// Create a new span element to hold the reading time text
const readingTimeSpan = document.createElement('span');
readingTimeSpan.textContent = ` ${readingTime}-Minute Read`;

// Create a new SVG element
const svgElement = document.createElementNS("http://www.w3.org/2000/svg", "svg");
svgElement.setAttribute("xmlns", "http://www.w3.org/2000/svg");
svgElement.setAttribute("width", "16");
svgElement.setAttribute("height", "16");
svgElement.setAttribute("fill", "currentColor");
svgElement.setAttribute("class", "bi bi-stopwatch");
svgElement.setAttribute("viewBox", "0 0 16 16");

// Add the path elements to the SVG
const path1 = document.createElementNS("http://www.w3.org/2000/svg", "path");
path1.setAttribute("d", "M8.5 5.6a.5.5 0 1 0-1 0v2.9h-3a.5.5 0 0 0 0 1H8a.5.5 0 0 0 .5-.5z");

const path2 = document.createElementNS("http://www.w3.org/2000/svg", "path");
path2.setAttribute("d", "M6.5 1A.5.5 0 0 1 7 .5h2a.5.5 0 0 1 0 1v.57c1.36.196 2.594.78 3.584 1.64a.715.715 0 0 1 .012-.013l.354-.354-.354-.353a.5.5 0 0 1 .707-.708l1.414 1.415a.5.5 0 1 1-.707.707l-.353-.354-.354.354a.512.512 0 0 1-.013.012A7 7 0 1 1 7 2.071V1.5a.5.5 0 0 1-.5-.5M8 3a6 6 0 1 0 .001 12A6 6 0 0 0 8 3");

// Append the path elements to the SVG
svgElement.appendChild(path1);
svgElement.appendChild(path2);

// Append the SVG and reading time span to the 'readingTime' div
const readingTimeDiv = document.getElementById('readingTime');
readingTimeDiv.innerHTML = ''; // Clear existing content
readingTimeDiv.appendChild(svgElement);
readingTimeDiv.appendChild(readingTimeSpan);
