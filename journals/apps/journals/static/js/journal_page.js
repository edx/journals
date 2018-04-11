/* This is not how we want to do things long term */
journal_structure = journal_structure['journal_structure'];

function getTOCLayerHTML(layer){
    var retHTML = '<li><a href="' + layer.url +'">' + layer.title + '</a></li>';
    if(layer.children){
        retHTML += '<ul>' + layer.children.map((child) => getTOCLayerHTML(child)).join("") + '</ul>';
    }
    console.log(retHTML)
    return retHTML;
}

function getTOCHTML(){
    var retHTML = '<ul>' + journal_structure.map((child) => getTOCLayerHTML(child)).join("") + '</ul>';
    return retHTML;
}

document.getElementsByClassName('toc-journal-struct')[0].innerHTML = getTOCHTML()
