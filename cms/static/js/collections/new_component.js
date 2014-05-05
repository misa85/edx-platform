define(["backbone", "js/models/new_component"], function(Backbone, NewComponentModel) {
    var NewComponentCollection = Backbone.Collection.extend({
        model : NewComponentModel
    });
    return NewComponentCollection;
});
