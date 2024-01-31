let blogPosts = [];
    
async function fetchBlogPosts() {
try {
    const response = await fetch('../../assets/search-cards.json');
    const data = await response.json();
    return data;
    } catch (error) {
        console.error('Error fetching JSON data:', error);
    }
}

function renderBlogPost(post) {
    const card = document.createElement("div");

    card.classList.add("col-xs-12");
    card.classList.add("col-sm-12");
    card.classList.add("col-md-6");
    card.classList.add("col-lg-4");
    card.classList.add("col-xlg-3");

// <img style="height: 250px;" src="${post.image}" class="img-fluid" alt="Blog Post Image">

card.innerHTML = `
    <div class="card shadow-lg mb-4" style="border-radius: 20px; overflow: hidden;">
    <div class="card-body">
        <a href="${post.url}" style="text-decoration: none;" target="_blank"><h2 class="card-title h4 gradient">${post.title}</h2></a>
        ${post.keywords.map(keyword => `<span style="margin-right: 5px;" class="card-keyword badge rounded-pill bg-info text-dark">${keyword}</span>`).join('')}
        <hr class='mt-4'>
        <p class="card-text mt-2 mb-2">${post.description}</p>
        <a href="${post.url}" style="text-decoration: none;" target="_blank">
            <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
        </a>
    </div>
    </div>
`;

return card;
}

function renderAllBlogPosts(posts) {
    const container = document.getElementById("blogPostsContainer");
    container.innerHTML = "";

    posts.forEach(post => {
        const card = renderBlogPost(post);
        container.appendChild(card);
    });
}


function filterBlogPosts(keyword) {
    const filteredPosts = blogPosts.filter(post => {
        const cardTitle = post.title.toLowerCase();
        const cardCategory = post.category.toLowerCase();
        const cardSummary = (post.summary || []).join(' ').toLowerCase(); // Handle the case where summary is undefined
        // Check if the keyword is present in the card title, summary, or keywords
        return cardTitle.includes(keyword.toLowerCase()) ||
            cardSummary.includes(keyword.toLowerCase()) ||
            cardCategory.includes(keyword.toLowerCase()) ||
            post.keywords.some(k => k.toLowerCase().includes(keyword.toLowerCase()));
    });
    renderAllBlogPosts(filteredPosts);
}


async function init() {
    blogPosts = await fetchBlogPosts();
    renderAllBlogPosts(blogPosts);
}

init();

document.getElementById("searchBar").addEventListener("input", function (event) {
    const keyword = event.target.value.trim();
    filterBlogPosts(keyword);
});