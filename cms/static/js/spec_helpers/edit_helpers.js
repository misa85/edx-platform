/**
 * Provides helper methods for invoking Studio editors in Jasmine tests.
 */
define(["jquery", "underscore", "js/spec_helpers/create_sinon", "js/spec_helpers/modal_helpers",
    "js/views/modals/edit_xblock", "xmodule", "coffee/src/main", "xblock/cms.runtime.v1"],
    function($, _, create_sinon, modal_helpers, EditXBlockModal) {

        var installMockXBlock, uninstallMockXBlock, installMockXModule, uninstallMockXModule,
            installEditTemplates, showEditModal;

        installMockXBlock = function(mockResult) {
            window.MockXBlock = function(runtime, element) {
                return {
                    runtime: runtime
                };
            };
        };

        uninstallMockXBlock = function() {
            window.MockXBlock = null;
        };

        installMockXModule = function(mockResult) {
            window.MockDescriptor = _.extend(XModule.Descriptor, {
                save: function() {
                    return mockResult;
                }
            });
        };

        uninstallMockXModule = function() {
            window.MockDescriptor = null;
        };

        installEditTemplates = function(append) {
            modal_helpers.installModalTemplates(append);

            // Add templates needed by the edit XBlock modal
            modal_helpers.installTemplate('edit-xblock-modal');
            modal_helpers.installTemplate('editor-mode-button');

            // Add templates needed by the settings editor
            modal_helpers.installTemplate('metadata-editor');
            modal_helpers.installTemplate('metadata-number-entry');
            modal_helpers.installTemplate('metadata-string-entry');
        };

        showEditModal = function(requests, xblockElement, model, mockHtml, options) {
            var modal = new EditXBlockModal({});
            modal.edit(xblockElement, model, options);
            create_sinon.respondWithJson(requests, {
                html: mockHtml,
                "resources": []
            });
            return modal;
        };

        return $.extend(modal_helpers, {
            'installMockXBlock': installMockXBlock,
            'uninstallMockXBlock': uninstallMockXBlock,
            'installMockXModule': installMockXModule,
            'uninstallMockXModule': uninstallMockXModule,
            'installEditTemplates': installEditTemplates,
            'showEditModal': showEditModal
        });
    });
