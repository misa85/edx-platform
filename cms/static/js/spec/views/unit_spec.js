define(["jquery", "coffee/src/views/unit", "js/models/module_info", "js/views/feedback_notification",
    "js/collections/new_component", "js/spec_helpers/create_sinon", "js/spec_helpers/view_helpers",
    "jasmine-stealth"],
    function ($, UnitEditView, ModuleModel, NotificationView, NewComponentCollection,
              create_sinon, view_helpers) {
        var requests, unit, initialize, respondWithHtml, verifyJSON, verifyComponents, i;

        respondWithHtml = function(html) {
            var requestIndex = requests.length - 1;
            create_sinon.respondWithJson(
                requests,
                { html: html, "resources": [] },
                requestIndex
            );
        };

        initialize = function(test) {
            var mockXBlockHtml = readFixtures('mock/mock-unit-page-xblock.underscore');
            requests = create_sinon.requests(test);
            unit = new UnitEditView({
                el: $('.main-wrapper'),
                newComponentCollection: new NewComponentCollection([
                    [["Discussion", "discussion", false, null]]
                ], {parse: true}),
                model: new ModuleModel({
                    id: 'unit_locator',
                    state: 'draft'
                })
            });
            respondWithHtml(mockXBlockHtml);
        };

        verifyJSON = function (requests, json) {
            var request = requests[requests.length - 1];
            expect(request.url).toEqual("/xblock");
            expect(request.method).toEqual("POST");
            // There was a problem with order of returned parameters in strings.
            // Changed to compare objects instead strings.
            expect(JSON.parse(request.requestBody)).toEqual(JSON.parse(json));
        };

        verifyComponents = function (unit, locators) {
            var components = unit.$(".component");
            expect(components.length).toBe(locators.length);
            for (i = 0; i < locators.length; i++) {
                expect($(components[i]).data('locator')).toBe(locators[i]);
            }
        };

        describe("UnitEditView", function() {
            beforeEach(function() {
                view_helpers.installViewTemplates();
                view_helpers.installTemplate('add-xblock-component');
                view_helpers.installTemplate('add-xblock-component-button');
                view_helpers.installTemplate('add-xblock-component-menu');
                view_helpers.installTemplate('add-xblock-component-menu-problem');
                appendSetFixtures(readFixtures('mock/mock-unit-page.underscore'));
            });

            describe('duplicateComponent', function() {
                var clickDuplicate;

                clickDuplicate = function (index) {
                    unit.$(".duplicate-button")[index].click();
                };

                it('sends the correct JSON to the server', function () {
                    initialize(this);
                    clickDuplicate(0);
                    verifyJSON(requests, '{"duplicate_source_locator":"loc_1","parent_locator":"unit_locator"}');
                });

                it('inserts duplicated component immediately after source upon success', function () {
                    initialize(this);
                    clickDuplicate(0);
                    create_sinon.respondWithJson(requests, {"locator": "duplicated_item"});
                    verifyComponents(unit, ['loc_1', 'duplicated_item', 'loc_2']);
                });

                it('inserts duplicated component at end if source at end', function () {
                    initialize(this);
                    clickDuplicate(1);
                    create_sinon.respondWithJson(requests, {"locator": "duplicated_item"});
                    verifyComponents(unit, ['loc_1', 'loc_2', 'duplicated_item']);
                });

                it('shows a notification while duplicating', function () {
                    initialize(this);
                    clickDuplicate(0);
                    expect(view_helpers.getNotificationMessage()).toBe('Duplicating\u2026');
                    create_sinon.respondWithJson(requests, {"locator": "duplicated_item"});
                    expect(view_helpers.getNotificationMessage()).toBeNull();
                });

                it('does not insert duplicated component upon failure', function () {
                    initialize(this);
                    clickDuplicate(0);
                    create_sinon.respondWithError(requests);
                    verifyComponents(unit, ['loc_1', 'loc_2']);
                });
            });

            describe('createNewComponent ', function () {
                var clickNewComponent;

                clickNewComponent = function () {
                    unit.$(".new-component .new-component-type a.single-template").click();
                };

                it('sends the correct JSON to the server', function () {
                    initialize(this);
                    clickNewComponent();
                    verifyJSON(requests, '{"category":"discussion","type":"discussion","parent_locator":"unit_locator"}');
                });

                it('inserts new component at end', function () {
                    initialize(this);
                    clickNewComponent();
                    create_sinon.respondWithJson(requests, {"locator": "new_item"});
                    verifyComponents(unit, ['loc_1', 'loc_2', 'new_item']);
                });

                it('shows a notification while creating', function () {
                    initialize(this);
                    clickNewComponent();
                    expect(view_helpers.getNotificationMessage()).toBe('Adding\u2026');
                    create_sinon.respondWithJson(requests, {"locator": "new_item"});
                    expect(view_helpers.getNotificationMessage()).toBeNull();
                });

                it('does not insert duplicated component upon failure', function () {
                    initialize(this);
                    clickNewComponent();
                    create_sinon.respondWithError(requests);
                    verifyComponents(unit, ['loc_1', 'loc_2']);
                });
            });

            describe("Disabled edit/publish links during ajax call", function() {
                var link,
                    draft_states = [
                        {
                            state: "draft",
                            selector: ".publish-draft"
                        },
                        {
                            state: "public",
                            selector: ".create-draft"
                        }
                    ],
                    editLinkFixture =
                        '<div class="main-wrapper edit-state-draft" data-locator="unit_locator"> \
                          <div class="unit-settings window"> \
                            <h4 class="header">Unit Settings</h4> \
                            <div class="window-contents"> \
                              <div class="row published-alert"> \
                                <p class="edit-draft-message"> \
                                  <a href="#" class="create-draft">edit a draft</a> \
                                </p> \
                                <p class="publish-draft-message"> \
                                  <a href="#" class="publish-draft">replace it with this draft</a> \
                                </p> \
                              </div> \
                            </div> \
                          </div> \
                        </div>';
                function test_link_disabled_during_ajax_call(draft_state) {
                    beforeEach(function () {
                        appendSetFixtures(editLinkFixture);
                        // needed to stub out the ajax
                        window.analytics = jasmine.createSpyObj('analytics', ['track']);
                        window.course_location_analytics = jasmine.createSpy('course_location_analytics');
                        window.unit_location_analytics = jasmine.createSpy('unit_location_analytics');
                    });

                    it("re-enables the " + draft_state['selector'] + " link once the ajax call returns", function() {
                        initialize();
                        runs(function() {
                            spyOn($, "ajax").andCallThrough();
                            spyOn($.fn, 'addClass').andCallThrough();
                            spyOn($.fn, 'removeClass').andCallThrough();
                            link = $(draft_state['selector']);
                            link.click();
                        });
                        waitsFor(function() {
                            // wait for "is-disabled" to be removed as a class
                            return !($(draft_state['selector']).hasClass("is-disabled"));
                        }, 500);
                        runs(function() {
                            // check that the `is-disabled` class was added and removed
                            expect($.fn.addClass).toHaveBeenCalledWith("is-disabled");
                            expect($.fn.removeClass).toHaveBeenCalledWith("is-disabled");

                            // make sure the link finishes without the `is-disabled` class
                            expect(link).not.toHaveClass("is-disabled");

                            // affirm that ajax was called
                            expect($.ajax).toHaveBeenCalled();
                        });
                    });
                }
                for (var i = 0; i < draft_states.length; i++) {
                    test_link_disabled_during_ajax_call(draft_states[i]);
                }
            });
        })
    }
);
