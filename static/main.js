// Grab the character media from our API endpoint
async function getCharacterMedia(vaId) {
    try {
        const response = await axios.get(`/api/character_media/${vaId}`);
        return response.data;
    } catch (error) {
        console.error(error);
    }
}

// Function to get a nested property value from an object
function getNestedAttr(obj, attr) {
    return attr.split('.').reduce((o, key) => o && o[key], obj);
}

// Function to sort the media by a given attribute, in ascending or descending order
function sortMedia(media, attr, order = 'asc') {
    console.log('Sorting by:', attr, 'Order:', order);
    // Returns the sorted array. [...media] creates a new array that is a copy of media. This is to prevent modifying the original media array because the sort function sorts in place.
    return [...media].sort((a, b) => {
        // Call parseFloat to convert values to a number
        let attrA = getNestedAttr(a, attr);
        let attrB = getNestedAttr(b, attr);
        if (order === 'asc') {
            return attrA - attrB;
        } else {
            return attrB - attrA;
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

    // Default values
    let characterImg = '<p>No image available</p>';
    let seriesImg = '';
    let characterName = '<h5 class="character">Unknown Character</h5>';

    // If character and character image exist, create character img tag
    if (character && character.image) {
        characterImg = `<img src="${character.image.large}" alt="${character.name.full}" class="character-img img-fluid" />`;
    }

    // If cover image exists, create series img tag
    if (media.node.coverImage) {
        seriesImg = `<img src="${media.node.coverImage.medium}" alt="${media.node.title.romaji}" class="series-img img-fluid" />`;
    }

    // If character and character name exist, create h5 tag
    if (character && character.name) {
        characterName = `<h5 class="character">${character.name.full}</h5>`;
    }

    // Do userListScore & userListStatus exist for this media?
    let userListScore = media.node.userListScore
        ? `<p>User Score: ${media.node.userListScore}</p>`
        : '';
    let userListStatus = media.node.userListStatus
        ? `<p>User Status: ${media.node.userListStatus}</p>`
        : '';

    // Constructing the card with the gathered information
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
                    <p>Score: ${media.node.averageScore}</p>
                    <p>Popularity: ${media.node.popularity}</p>
                    ${userListScore}
                    ${userListStatus}
                    AL Link: <a href="https://anilist.co/anime/${media.node.id}">Link</a>
                </div>
            </div>
        </div>`;
    return html;
}

// DEPRECATED: Load and sort the media
async function loadAndSortMedia(vaId, attr, order = 'asc') {
    try {
        const media = await getCharacterMedia(vaId);
        const sortedMedia = sortMedia(media, attr, order);
        return sortedMedia;
    } catch (error) {
        console.error(error);
    }
}

// DEPRECATED: Sort the media by season year, in ascending or descending order
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
