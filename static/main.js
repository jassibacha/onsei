// Grab the character media from our API endpoint
async function getCharacterMedia(vaId) {
    try {
        const response = await axios.get(`/api/character_media/${vaId}`);
        return response.data;
    } catch (error) {
        console.error(error);
    }
}

// Sort the media by season year, in ascending or descending order
function sortMediaBySeasonYear(media, order = 'asc') {
    return media.sort((a, b) => {
        // Ascending order by default
        if (order === 'asc') {
            return a.node.seasonYear - b.node.seasonYear;
        }
        // Descending order
        else if (order === 'desc') {
            return b.node.seasonYear - a.node.seasonYear;
        }
    });
}

// Display character media after we've pulled it all!
function displayCharacterMedia(charMedia) {
    for (let media of charMedia) {
        let html = createMediaCard(media);
        $('.roles').append(html);
    }
}

// Function to display the 'Media Card'
function createMediaCard(media) {
    // We first store the character in a variable for readability.
    let character = media.characters[0];

    let characterImg = '';
    // Then, we check if the character is defined and if it has an image.
    if (character && character.image) {
        // If both conditions are met, we create an img tag with the character's image.
        characterImg = `<img src="${character.image.large}" alt="${character.name.full}" class="character-img img-fluid" />`;
    } else {
        // Otherwise, we display a message saying no image is available.
        characterImg = '<p>No image available</p>';
    }

    let seriesImg = '';
    // Here we check if the media node has a cover image.
    if (media.node.coverImage) {
        // If it does, we create an img tag with the cover image.
        seriesImg = `<img src="${media.node.coverImage.medium}" alt="${media.node.title.romaji}" class="series-img img-fluid" />`;
        // Note: We don't need an else statement here because seriesImg is already an empty string.
    }

    let characterName = '';
    // Similar to the character image, we check if the character and its name are defined.
    if (character && character.name) {
        // If they are, we create a h5 tag with the character's name.
        characterName = `<h5 class="character">${character.name.full}</h5>`;
    } else {
        // Otherwise, we display a message saying the character's name is unknown.
        characterName = '<h5 class="character">Unknown Character</h5>';
    }

    // We then create the HTML string with all the parts we created above.
    let html = `
        <div class="col-sm-6 col-md-4 col-lg-3">
            <div class="card card-role">
                <div class="card-body">
                    <div class="img-wrap mb-3">
                        ${characterImg}
                        ${seriesImg}
                    </div>
                    ${characterName}
                    <div class="series">${media.node.title.romaji}</div>
                    <p>Year: ${media.node.seasonYear}</p>
                    AL Link: <a href="https://anilist.co/anime/${media.node.id}">Link</a>
                </div>
            </div>
        </div>`;
    // Finally, we return the HTML string.
    return html;
}

// Attempt 1 to try and do the pulling and sorting by year in one call
async function loadAndSortMedia(vaId) {
    try {
        const media = await getCharacterMedia(vaId);
        const sortedMedia = sortMediaBySeasonYear(media);
        return sortedMedia;
    } catch (error) {
        console.error(error);
    }
}
