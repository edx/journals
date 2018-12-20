function(modal) {
	$('button.insert-code').on('click', function (event) {
		modal.respond('insertedCodeBlock', {'code': $('#id_insert_code_block').val()});
		modal.close();
	});
}
