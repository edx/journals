function(modal) {
    modal.respond('videoChosen', {{ video_json|safe }});
    modal.close();
}
