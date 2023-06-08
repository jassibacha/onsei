// Grab the character media from our API endpoint
async function getCharacterMedia(vaId) {
    try {
        const response = await axios.get(`/api/character_media/${vaId}`, {
            headers: {
                Authorization: 'Bearer wnYW3pY6b/pmAsNur?sbx=EOrTDKqslHIGjG',
            },
        });

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
        characterImgUrl = `${character.image.large}`;
    }

    // If cover image exists, create series img tag
    if (media.node.coverImage) {
        seriesImg = `<img src="${media.node.coverImage.medium}" alt="${media.node.title.romaji}" class="series-img img-fluid" />`;
    }

    // If character and character name exist, create h5 tag
    if (character && character.name) {
        characterName = `<strong>${character.name.full}</strong>`;
        //characterName = `<h5 class="character">${character.name.full}</h5>`;
    }

    // Do userListScore & userListStatus exist for this media?
    let userListScore = media.node.userListScore
        ? `Score: ${media.node.userListScore}`
        : '';

    let badgeClass;
    if (media.node.userListStatus === 'COMPLETED') {
        badgeClass = 'bg-success';
    } else if (media.node.userListStatus === 'CURRENT') {
        badgeClass = 'bg-purple';
    } else {
        badgeClass = '';
    }
    let userListStatus = media.node.userListStatus
        ? `<span class="badge ${badgeClass}">${media.node.userListStatus}</span>`
        : '';

    // let userListStatus = media.node.userListStatus
    //     ? `<span class="badge">${media.node.userListStatus}</span>`
    //     : '';

    // Constructing the card with the gathered information
    let html = `
        <div class="col-6 col-md-4 col-lg-3 col-xl-2 col-xxl-2">
            <div class="card card-role mb-3">
                <div class="card-img-top img-wrap d-flex align-items-center">
                    ${characterImg}
                    ${seriesImg}
                    <div class="blur-bg" style="background-image:url('${characterImgUrl}')"></div>
                </div>
                <div class="card-body">
                    <div class="name">
                    ${characterName}
                    </div>
                    <a href="/series/${
                        media.node.id
                    }" class="series d-block small mb-2">
                    ${media.node.title.english || media.node.title.romaji}
                    </a>
                    <div class="info d-flex flex-row justify-content-between">
                        <div class="">
                            <div class="title">Year</div>
                            <div class="year">
                            ${media.node.seasonYear}
                            </div>
                            <div class="title">Users</div>
                            <div class="popularity">
                            ${formatNumber(media.node.popularity)}
                            </div>
                        </div>
                        <div class="text-center">
                            <div class="title mb-0 text-center">Score</div>
                            <div class="score d-flex ${getScoreClass(
                                media.node.averageScore
                            )}">${media.node.averageScore}</div>
                        </div>
                    </div>
                    
                </div>
                    <ul class="userlist list-group list-group-flush">
                        <li class="list-group-item d-flex justify-content-between align-items-center">${userListScore} ${userListStatus}</li>
                    </ul>
            </div>
        </div>`;
    return html;
}
/*

<div class="info d-flex flex-row">
    <div class="col-7 col-sm-8">

    </div>
    <div class="col-5 col-sm-4 text-center">

    </div>
</div>

*/

/* *****************************
 ** */
// Grab the series characters and roles from our API endpoint
async function getSeriesRoles(seriesId) {
    try {
        const response = await axios.get(`/api/series_roles/${seriesId}`, {
            headers: {
                Authorization: 'Bearer wnYW3pY6b/pmAsNur?sbx=EOrTDKqslHIGjG',
            },
        });

        return response.data;
    } catch (error) {
        console.error(error);
    }
}

// Display character media after we've pulled it all!
function displaySeriesRoles(seriesRoles) {
    for (let char of seriesRoles) {
        let html = createRoleCard(char);
        $('.characters').append(html);
    }

    // Declare these after creation to allow bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll(
        '[data-bs-toggle="tooltip"]'
    );
    const tooltipList = [...tooltipTriggerList].map(
        (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl)
    );
}

// Function to display the 'Media Card'
function createRoleCard(char) {
    let characterName = 'N/A';
    let voiceActorName = 'N/A';
    let characterImage = '/static/img/character-empty.jpg';
    let voiceActorImage = '/static/img/va-empty.jpg';
    let voiceActorId = 'N/A';
    let voiceActorCharacters = '';

    if (char.node) {
        if (char.node.name && char.node.name.full) {
            characterName = char.node.name.full;
        }
        if (char.node.image && char.node.image.medium) {
            characterImage = char.node.image.medium;
        }
    }

    if (char.voiceActors && char.voiceActors.length > 0) {
        if (char.voiceActors[0].name && char.voiceActors[0].name.full) {
            voiceActorName = char.voiceActors[0].name.full;
        }
        if (char.voiceActors[0].image && char.voiceActors[0].image.medium) {
            voiceActorImage = char.voiceActors[0].image.medium;
        }
        voiceActorId = char.voiceActors[0].id;

        // Check if voice actor has characters
        if (
            char.voiceActors[0].characters &&
            char.voiceActors[0].characters.nodes
        ) {
            // Iterate over characters
            char.voiceActors[0].characters.nodes.forEach((character) => {
                voiceActorCharacters += `
                <div class="character w-20">
                    <div class="img-wrap d-flex align-items-center" data-bs-toggle="tooltip" data-bs-title="${character.name.full}">
                        <img src="${character.image.medium}" alt="${character.name.full}" class="img-fluid" />
                        <div class="overlay px-2">
                        ${character.name.full}
                        </div>
                    </div>
                </div>`;
            });
        }
    }

    // <div class="col-sm-6 col-lg-4 mb-3">
    let html = `
        <div class="col-sm-12 col-md-6 col-lg-4 mb-3">
            <div class="card card-character">
                <div class="card-top d-flex flex-row">
                    <div class="col-6 left">
                        <img src="${characterImage}" class="char-img" alt="${characterName}" />
                        <span class="character-text ps-2 pe-1">${characterName}</span>
                    </div>
                    <div class="col-6 right">
                        <a href="/va/${voiceActorId}" class="justify-content-end text-end">
                            <span class="character-text text-end ps-1 pe-2">${voiceActorName}</span>
                            <img src="${voiceActorImage}" class="va-img" alt="${voiceActorName}" />
                        </a>
                    </div>
                </div>
                <div class="popular-roles">
                    <div class="title">Popular Roles:</div>
                    <div class="d-flex flex-row">
                    ${voiceActorCharacters}
                    </div>
                </div>
            </div>
        </div>`;
    return html;
}

// Number formatting for popularity display
function formatNumber(number) {
    if (number >= 1000) {
        return (number / 1000).toFixed(1) + 'k'; // convert to K for number from > 1000 < 1 million
    } else {
        return number; // if value < 1000, nothing to do so return the same number
    }
}

// Taking a score and getting a css class for background color
function getScoreClass(score) {
    // normalize scores that are between 0-10 and 0-10 with decimals to 0-100
    if (score <= 10) {
        score *= 10;
    }

    if (score >= 0 && score <= 20) return 'score-red';
    else if (score >= 21 && score <= 40) return 'score-orange';
    else if (score >= 41 && score <= 60) return 'score-yellow-orange';
    else if (score >= 61 && score <= 80) return 'score-yellow-green';
    else if (score >= 81 && score <= 100) return 'score-green';
    else return '';
}

// // DEPRECATED: Load and sort the media
// async function loadAndSortMedia(vaId, attr, order = 'asc') {
//     try {
//         const media = await getCharacterMedia(vaId);
//         const sortedMedia = sortMedia(media, attr, order);
//         return sortedMedia;
//     } catch (error) {
//         console.error(error);
//     }
// }

// // DEPRECATED: Sort the media by season year, in ascending or descending order
// function sortMediaBySeasonYear(media, order = 'asc') {
//     return media.sort((a, b) => {
//         // Ascending order by default
//         if (order === 'asc') {
//             return a.node.seasonYear - b.node.seasonYear;
//         }
//         // Descending order
//         else if (order === 'desc') {
//             return b.node.seasonYear - a.node.seasonYear;
//         }
//     });
// }
