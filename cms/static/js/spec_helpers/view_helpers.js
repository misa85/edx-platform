/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(["jquery"],
    function($) {
        var installTemplate, installViewTemplates, getNotificationMessage;

        installTemplate = function(templateName, isFirst) {
            var template = readFixtures(templateName + '.underscore'),
                templateId = templateName + '-tpl';
            if (isFirst) {
                setFixtures($("<script>", { id: templateId, type: "text/template" }).text(template));
            } else {
                appendSetFixtures($("<script>", { id: templateId, type: "text/template" }).text(template));
            }
        };

        installViewTemplates = function(append) {
            installTemplate('system-feedback', !append);
            appendSetFixtures('<div id="page-notification"></div>');
        };

        getNotificationMessage = function() {
            var notificationPanel = $('.wrapper-notification');
            if (notificationPanel.length === 0 || notificationPanel.hasClass('is-hiding')) {
                return null;
            }
            return notificationPanel.find('h2').text();
        };

        return {
            'installTemplate': installTemplate,
            'installViewTemplates': installViewTemplates,
            'getNotificationMessage': getNotificationMessage
        };
    });
