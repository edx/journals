(function() {
	(function ($) {
		return $.widget('IKS.hallowagtailcodeblock', {
			options: {
				uuid: '',
				editable: null
			},
			populateToolbar: function (toolbar) {
				var codeButton, widget, getEnclosingCode, codeBlock, removerAllChildren;

				widget = this;
				codeButton = $('<span class="' + this.widgetName + '"></span>');
				getEnclosingCode = function () {
					var node = widget.options.editable.getSelection().commonAncestorContainer;
					return $(node).parents('code').get(0);
				};
				removerAllChildren = function (node) {
					while (node.firstChild) {
						node.removeChild(node.firstChild);
					}
				};
				codeButton.hallobutton({
					uuid: this.options.uuid,
					editable: this.options.editable,
					label: 'CodeBlock',
					icon: 'icon-code',
					command: null,
					queryState: function (event) {
						return codeButton.hallobutton('checked', !!getEnclosingCode());
					}
				});
				toolbar.append(codeButton);
				return codeButton.on('click', function (event) {
					var urlParams = {};
					var lastSelection = widget.options.editable.getSelection();
					var enclosingCode = getEnclosingCode();
					if (enclosingCode) {
						urlParams['code_block'] = $(enclosingCode).text();
					} else if (!lastSelection.collapsed) {
						urlParams['code_block'] = lastSelection.toString();
					}

					return ModalWorkflow({
						url: window.chooserUrls.insertCodeBlock,
						urlParams: urlParams,
						responses: {
							insertedCodeBlock: function (data) {
								var pre, code;
								var codeBlock = document.createTextNode(data.code);
								if (enclosingCode) {
									// Editing an existing code block
									code = enclosingCode;
									removerAllChildren(code);
									pre = $(code).parents('pre').get(0);
								} else if (!lastSelection.collapsed) {
									// Turning a selection into a code block
									pre = document.createElement('pre');
									code = document.createElement('code');
									pre.appendChild(code);
									var nodesInSelection = lastSelection.getNodes();
									if (nodesInSelection.length > 0) {
										var parentNode = nodesInSelection[0].parentNode;
										removerAllChildren(parentNode);
										parentNode.appendChild(pre);
									}
								} else {
									pre = document.createElement('pre');
									code = document.createElement('code');
									pre.appendChild(code);
									lastSelection.insertNode(pre);
								}
								code.appendChild(codeBlock);
								hljs.highlightBlock(pre);
								return widget.options.editable.element.trigger('change');
							}
						}
					});
				});
			}
		});
	})(jQuery);

}).call(this);
