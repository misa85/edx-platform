(function (undefined) {
    describe('VideoVolumeControl', function () {
        var state, oldOTBD, volumeControl;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                .andReturn(null);
        });

        afterEach(function () {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
            state.storage.clear();
        });

        describe('constructor', function () {
            beforeEach(function () {
                spyOn($.fn, 'slider').andCallThrough();
                $.cookie.andReturn('75');
                state = jasmine.initializePlayer();
                volumeControl = state.videoVolumeControl;
            });

            it('initialize volume to 75%', function () {
                expect(volumeControl.volume).toEqual(75);
            });

            it('render the volume control', function () {
                expect(state.videoControl.secondaryControlsEl.html())
                    .toContain("<div class=\"volume\">\n");
            });

            it('create the slider', function () {
                expect($.fn.slider).toHaveBeenCalledWith({
                    orientation: "vertical",
                    range: "min",
                    min: 0,
                    max: 100,
                    value: volumeControl.volume,
                    slide: volumeControl.onSlideHandler
                });
                expect($.fn.slider).toHaveBeenCalledWith('value', volumeControl.volume);
            });

            it('add ARIA attributes to live region', function () {
                var liveRegion = $('.video-live-region');

                expect(liveRegion).toHaveAttrs({
                    'role': 'status',
                    'aria-live': 'polite',
                    'aria-atomic': 'false'
                });
            });

            it('add ARIA attributes to volume control', function () {
                var button = $('.volume > a');

                expect(button).toHaveAttrs({
                    'role': 'button',
                    'title': 'Volume',
                    'aria-disabled': 'false'
                });
            });

            it('bind the volume control', function () {
                var button = $('.volume > a');

                expect(button).toBeEventBinded('keydown');
                expect(button).toBeEventBinded('mousedown');

                expect($('.volume')).not.toHaveClass('is-opened');

                $('.volume').mouseenter();
                expect($('.volume')).toHaveClass('is-opened');

                $('.volume').mouseleave();
                expect($('.volume')).not.toHaveClass('is-opened');
            });
        });

        describe('setVolume', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                volumeControl = state.videoVolumeControl;

                this.addMatchers({
                    assertLiveRegionState: function (volume, expectation) {
                        var region = $('.video-live-region');

                        var getExpectedText = function (text) {
                            return text + ' Volume.'
                        };

                        this.actual.setVolume(volume, true, true);
                        return region.text() === getExpectedText(expectation);
                    }
                });
            });

            describe('when the new volume is more than 0', function () {
                beforeEach(function () {
                    volumeControl.setVolume(60, false, true);
                });

                it('set the player volume', function () {
                    expect(volumeControl.volume).toEqual(60);
                });

                it('remote muted class', function () {
                    expect($('.volume')).not.toHaveClass('is-muted');
                });
            });

            describe('when the new volume is 0', function () {
                beforeEach(function () {
                    volumeControl.setVolume(0, false, true);
                });

                it('set the player volume', function () {
                    expect(volumeControl.volume).toEqual(0);
                });

                it('add muted class', function () {
                    expect($('.volume')).toHaveClass('is-muted');
                });
            });

            it('when the new volume is Muted', function () {
                expect(volumeControl).assertLiveRegionState(0, 'Muted');
            });

            it('when the new volume is in ]0,20]', function () {
                expect(volumeControl).assertLiveRegionState(10, 'Very low');
            });

            it('when the new volume is in ]20,40]', function () {
                expect(volumeControl).assertLiveRegionState(30, 'Low');
            });

            it('when the new volume is in ]40,60]', function () {
                expect(volumeControl).assertLiveRegionState(50, 'Average');
            });
            it('when the new volume is in ]60,80]', function () {
                expect(volumeControl).assertLiveRegionState(70, 'Loud');
            });
            it('when the new volume is in ]80,100[', function () {
                expect(volumeControl).assertLiveRegionState(90, 'Very loud');
            });
            it('when the new volume is Maximum', function () {
                expect(volumeControl).assertLiveRegionState(100, 'Maximum');
            });
        });

        describe('toggleMute', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                volumeControl = state.videoVolumeControl;
            });

            describe('when the current volume is more than 0', function () {
                beforeEach(function () {
                    volumeControl.volume = 60;
                    volumeControl.button.trigger('mousedown');
                });

                it('save the previous volume', function () {
                    expect(volumeControl.storedVolume).toEqual(60);
                });

                it('set the player volume', function () {
                    expect(volumeControl.volume).toEqual(0);
                });
            });

            describe('when the current volume is 0', function () {
                beforeEach(function () {
                    volumeControl.volume = 0;
                    volumeControl.storedVolume = 60;
                    volumeControl.button.trigger('mousedown');
                });

                it('set the player volume to previous volume', function () {
                    expect(volumeControl.volume).toEqual(60);
                });
            });
        });
    });
}).call(this);
