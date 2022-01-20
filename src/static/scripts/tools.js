function addCoords(document, name, data) {
    var coordinates = document.createElement('input')
    coordinates.setAttribute('type', 'hidden')
    coordinates.setAttribute('name', name)
    coordinates.setAttribute('value', JSON.stringify(Object.fromEntries(data)))
    return coordinates
}

function outOfBounds(x, y, width, height) {
    if (x < 0 || x > width || y < 0 || y > height) {
        return true
    }
    return false
}

function updateFormText(document, size) {
    document.getElementById('selected-coordinates').innerHTML =
        'Number of clicked locations: ' + size
}

function getSampleNumber() {
    NUMBER_OF_SAMPLES = 5
    return NUMBER_OF_SAMPLES
}
