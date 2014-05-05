define(["backbone"], function (Backbone) {
    /**
     * Simple model for adding a component of a given type (for example, "video" or "html").
     */
    var NewComponentModel = Backbone.Model.extend({
        defaults: {
            type: "",
            templates: []
        },
        parse: function (response) {
            this.templates = [];
            for (var i = 0; i !== response.length; i++) {
                var component_instance = response[i];
                var template_info = {};
                template_info.display_name = component_instance[0];
                template_info.template_name = component_instance[3];

                // This is only used for the problem type.
                template_info.is_simple = component_instance[2];

                this.templates.push(template_info);

                // The type of this component is the same for all instances within it.
                // We store the value from the first one.
                if (i === 0) {
                    this.type = component_instance[1];
                }

            }
        }
    });

    return NewComponentModel;
});
