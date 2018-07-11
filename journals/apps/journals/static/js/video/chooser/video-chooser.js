/* eslint-disable no-unused-vars, no-undef */
function createVideoChooser(id) {
	var $chooserElement = $('#' + id + '-chooser');
	var docTitle = $chooserElement.find('.title');
	var $input = $('#' + id);
	var editLink = $chooserElement.find('.edit-link');

	$('.action-choose', $chooserElement).click(function() {
		ModalWorkflow({
			url: window.chooserUrls.videoChooser,
			responses: {
				videoChosen: function(videoData) {
					$input.val(videoData.id);
					docTitle.text(videoData.display_name);
					$chooserElement.removeClass('blank');
					editLink.attr('href', videoData.edit_link);
				}
			}
		});
	});

	$('.action-clear', $chooserElement).click(function() {
		$input.val('');
		$chooserElement.addClass('blank');
	});
}
