$(function() {
    // We need to override the behavior from page-editor.js
    // To make the preview button work correctly for redirecting
    // to Journals Frontend App
	var $previewButton = $('.action-preview');
	var $clonedPreviewButton = $previewButton.clone();
	var $form = $('#page-edit-form');
	$previewButton[0].parentNode.replaceChild($clonedPreviewButton[0], $previewButton[0]);
	$previewButton = $clonedPreviewButton;
	var previewUrl = $previewButton.data('action');  // eslint-disable-line vars-on-top

	function setPreviewData() {
		return $.ajax({
			url: previewUrl,
			method: 'POST',
			data: new FormData($form[0]),
			processData: false,
			contentType: false
		});
	}

	$previewButton.click(function(e) {
		var $this = $(this);
		var $icon = $this.filter('.icon');
		var thisPreviewUrl = $this.data('action');
		var previewWindow = window.open('', thisPreviewUrl + '?' + Math.random().toString().slice(-8));
		e.preventDefault();
		$icon.addClass('icon-spinner').removeClass('icon-view');

		previewWindow.focus();

		setPreviewData().done(function(data) {
			if (data.is_valid) {
				previewWindow.document.location = thisPreviewUrl;
			} else {
				window.focus();
				previewWindow.close();
                // TODO: Stop sending the form, as it removes file data.
				$form.submit();
			}
		}).fail(function() {
			alert('Error while sending preview data.');  // eslint-disable-line no-alert
			window.focus();
			previewWindow.close();
		}).always(function() {
			$icon.addClass('icon-view').removeClass('icon-spinner');
		});
	});
});
