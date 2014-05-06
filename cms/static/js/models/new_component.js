define(["backbone"], function (Backbone) {
    /**
     * Simple model for adding a component of a given type (for example, "video" or "html").
     */
    return Backbone.Model.extend({
        defaults: {
            type: "",
            // Each entry in the template array is a dictionary with the following keys:
            // display_name, boilerplate_name (may be None), and is_common (only used for problems)
            templates: []
        },
        parse: function (response) {
            this.templates = [];
            for (var i = 0; i < response.length; i++) {
                var component_instance = response[i];
                var template_info = {};
                template_info.display_name = component_instance[0];
                template_info.boilerplate_name = component_instance[3];

                // This is only used for the problem type.
                template_info.is_common = component_instance[2];

                this.templates.push(template_info);

                // The type of this component is the same for all instances within it.
                // We store the value from the first one.
                if (i === 0) {
                    this.type = component_instance[1];
                }
            }
            // Sort the templates.
            this.templates.sort(function (a, b) {
                // The entry without a boilerplate always goes first
                if (!a.boilerplate_name || (a.display_name < b.display_name)) {
                    return -1;
                }
                else {
                    return (a.display_name > b.display_name) ? 1 : 0;
                }
            });
        }
    });
});
