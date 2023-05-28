// Grab the character media from our API endpoint
async function getCharacterMedia(vaId) {
    try {
        const response = await axios.get(`/api/character_media/${vaId}`);
        return response.data;
    } catch (error) {
        console.error(error);
    }
}

// Sort the media by season year, attempt 1
function sortMediaBySeasonYear(media) {
    return media.sort((a, b) => a.seasonYear - b.seasonYear);
}

// Display character media after we've pulled it all!
function displayCharacterMedia(charMedia) {
    // TODO: Improve this code to display the character media as desired.
    for (let media of charMedia) {
        $('.roles').append(`<p>${media.node.title.romaji}</p>`);
    }
}

// Attempt 1 to try and do the pulling and sorting by year in one call
async function loadAndSortMedia(vaId) {
    try {
        const media = await getCharacterMedia(vaId);
        const sortedMedia = sortMediaBySeasonYear(media);
        // Do something with sortedMedia
    } catch (error) {
        console.error(error);
    }
}
