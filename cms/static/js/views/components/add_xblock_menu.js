define(["jquery", "js/views/baseview"],
    function ($, BaseView) {

        var NewComponentMenu = BaseView.extend({
            className: function () {
                return "new-component-templates new-component-" + this.model.type;
            },
            initialize: function () {
                BaseView.prototype.initialize.call(this);
                var template_name = this.model.type === "problem" ? "add-xblock-component-menu-problem" :
                    "add-xblock-component-menu";
                this.template = this.loadTemplate(template_name);
                this.$el.html(this.template({type: this.model.type, templates: this.model.templates}));
                // Make the tabs on problems into "real tabs"
                $('.tab-group').tabs();
            }
        });

        return NewComponentMenu;
    }); // end define();