define(["jquery", "underscore", "js/views/baseview"],
    function ($, _, BaseView) {

        var NewComponentButton = BaseView.extend({
            tagName: "li",
            initialize : function() {
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate("add-xblock-component-button");
                this.$el.html(this.template({type: this.model.type, templates: this.model.templates}));
            }
        });

        return NewComponentButton;
    }); // end define();
