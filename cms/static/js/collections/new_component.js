define(["backbone", "js/models/new_component"], function(Backbone, NewComponentModel) {
    return Backbone.Collection.extend({
        model : NewComponentModel
    });
});
