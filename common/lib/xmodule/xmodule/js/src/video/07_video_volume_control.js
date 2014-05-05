(function(define) {
'use strict';
// VideoVolumeControl module.
define(
    'video/07_video_volume_control.js', [],
    function() {
        /**
         * Video speed control module.
         * @exports video/08_video_speed_control.js
         * @constructor
         * @param {object} state The object containing the state of the video
         * player.
         */
        var VolumeControl = function(state) {
            if (!(this instanceof VolumeControl)) {
                return new VolumeControl(state);
            }

            this.state = state;
            this.state.videoVolumeControl = this;
            this.initialize();

            return $.Deferred().resolve().promise();
        };

        VolumeControl.prototype = {
            min: 0,
            max: 100,
            step: 20,

            initialize: function() {
                this.el = this.state.el.find('.volume');

                if (this.state.isTouch) {
                    // iOS doesn't support volume change
                    this.el.remove();
                    return false;
                }
                // Youtube iframe react on key buttons and has his own handlers.
                // So, we disallow focusing on iframe.
                this.state.el.find('iframe').attr('tabindex', -1);
                this.button = this.el.children('a');
                this.a11y = new VolumeA11y(this.button, this.min, this.max);
                this.render();
                this.bindHandlers();
                this.setVolume(Cookie.getVolume(), true, false);
            },

            render: function() {
                var container = this.el.find('.volume-slider');

                this.volumeSlider = container.slider({
                    orientation: 'vertical',
                    range: 'min',
                    min: this.min,
                    max: this.max,
                    slide: this.onSlideHandler.bind(this)
                });

                // We provide an independent behavior to adjust volume level.
                // Therefore, we no need redundant focusing on slider in TAB
                // order.
                container.find('a').attr('tabindex', -1);
            },

            /** Bind any necessary function callbacks to DOM events. */
            bindHandlers: function() {
                this.state.el.on({
                    'keydown': this.keyDownHandler.bind(this),
                    'play': _.once(this.updateState.bind(this)),
                    'volumechange': this.onVolumeChangeHandler.bind(this)
                });
                this.el.on({
                    'mouseenter': this.openMenu.bind(this),
                    'mouseleave': this.closeMenu.bind(this)
                });
                this.button.on({
                    'click': false,
                    'mousedown': this.toggleMuteHandler.bind(this),
                    'keydown': this.keyDownButtonHandler.bind(this),
                    'focus': this.openMenu.bind(this),
                    'blur': this.closeMenu.bind(this)
                });
            },

            updateState: function(event) {
                this.setVolume(this.getVolume(), false, false);
            },

            getVolume: function() {
                return this.volume;
            },

            setVolume: function(volume, silent, withoutSlider) {

                if (volume === this.getVolume()) {
                    return false;
                }

                this.volume = volume;
                this.a11y.update(this.getVolume());

                if (!withoutSlider) {
                    this.updateSliderView(this.getVolume());
                }

                if (!silent) {
                    Cookie.setVolume(this.getVolume());
                    this.state.el.trigger('volumechange', [this.getVolume()]);
                }
            },

            increaseVolume: function() {
                var volume = Math.min(this.getVolume() + this.step, this.max);

                this.setVolume(volume, false, false);
            },

            decreaseVolume: function() {
                var volume = Math.max(this.getVolume() - this.step, this.min);

                this.setVolume(volume, false, false);
            },

            mute: function(muteStatus, silent) {
                var volume = 0;

                if (muteStatus === this.getMuteStatus()) {
                    return false;
                }

                this.isMuted = muteStatus;
                this.updateButtonView(this.getMuteStatus());

                if (this.getMuteStatus()) {
                    this.storedVolume = this.getVolume() || this.max;
                } else {
                    volume = this.storedVolume;
                }

                if (!silent) {
                    this.setVolume(volume, false, false);
                }
            },

            getMuteStatus: function () {
                return this.isMuted;
            },

            updateSliderView: function (volume) {
                this.volumeSlider.slider('value', volume);
            },

            updateButtonView: function(isMuted) {
                var action = isMuted ? 'addClass' : 'removeClass';
                // @TODO FIX class name
                this.el[action]('muted');
            },

            openMenu: function() {
                // @TODO move to closeMenu, FIX class name
                this.el.addClass('open');
            },

            closeMenu: function() {
                // @TODO move to closeMenu, FIX class name
                this.el.removeClass('open');
            },

            toggleMute: function() {
                this.mute(!this.getMuteStatus());
            },

            keyDownHandler: function(event) {
                // ALT key is used to change (alternate) the function of
                // other pressed keys. In this case, do nothing.
                if (event.altKey) {
                    return true;
                }

                if ($(event.target).hasClass('ui-slider-handle')) {
                    return true;
                }

                var KEY = $.ui.keyCode,
                    keyCode = event.keyCode;

                switch (keyCode) {
                    case KEY.UP:
                        // Shift + Arrows keyboard shortcut might be used by
                        // screen readers. In this case, do nothing.
                        if (event.shiftKey) {
                            return true;
                        }

                        this.increaseVolume();
                        return false;
                    case KEY.DOWN:
                        // Shift + Arrows keyboard shortcut might be used by
                        // screen readers. In this case, do nothing.
                        if (event.shiftKey) {
                            return true;
                        }

                        this.decreaseVolume();
                        return false;
                }

                return true;
            },

            keyDownButtonHandler: function(event) {
                // ALT key is used to change (alternate) the function of
                // other pressed keys. In this case, do nothing.
                if (event.altKey) {
                    return true;
                }

                var KEY = $.ui.keyCode,
                    keyCode = event.keyCode;

                switch (keyCode) {
                    case KEY.ENTER:
                    case KEY.SPACE:
                        this.toggleMute();

                        return false;
                }

                return true;
            },

            onSlideHandler: function(event, ui) {
                this.setVolume(ui.value, false, true);
            },

            toggleMuteHandler: function(event) {
                this.toggleMute();
                event.preventDefault();
            },

            onVolumeChangeHandler: function(event, volume) {
                if (volume <= this.min) {
                    this.mute(true, true);
                    this.state.el.off('volumechange.is-muted');
                    this.state.el.on('volumechange.is-muted', _.once(function () {
                        this.mute(false, true);
                    }.bind(this)));
                }
            }
        };


        var VolumeA11y = function (button, min, max) {
            this.min = min;
            this.max = max;
            this.button = button;
            this.i18n = {
                'Volume.': gettext('Volume'),
                // Translators: Volume level equals 0%.
                'Muted': gettext('Muted'),
                // Translators: Volume level in range (0,20]%
                'Very low': gettext('Very low'),
                // Translators: Volume level in range (20,40]%
                'Low': gettext('Low'),
                // Translators: Volume level in range (40,60]%
                'Average': gettext('Average'),
                // Translators: Volume level in range (60,80]%
                'Loud': gettext('Loud'),
                // Translators: Volume level in range (80,100)%
                'Very loud': gettext('Very loud'),
                // Translators: Volume level equals 100%.
                'Maximum': gettext('Maximum'),
            };

            this.initialize();
        };

        VolumeA11y.prototype = {
            initialize: function() {
                this.liveRegion = $('<div />', {
                    'class':  'sr video-live-region',
                    'role': 'status',
                    'aria-live': 'polite',
                    'aria-atomic': 'false'
                });

                this.button.after(this.liveRegion);
            },

            update: function(volume) {
                this.liveRegion.html([
                    this.getVolumeDescription(volume), this.i18n['Volume.']
                ].join(' '));
            },

            // Returns a string describing the level of volume.
            getVolumeDescription: function(volume) {
                if (volume === 0) {
                    return this.i18n['Muted'];
                } else if (volume <= 20) {
                    return this.i18n['Very low'];
                } else if (volume <= 40) {
                    return this.i18n['Low'];
                } else if (volume <= 60) {
                    return this.i18n['Average'];
                } else if (volume <= 80) {
                    return this.i18n['Loud'];
                } else if (volume <= 99) {
                    return this.i18n['Very loud'];
                }

                return this.i18n['Maximum'];
            }
        };


        var Cookie = {
            min: 0,
            max: 100,

            cookieName: 'video_player_volume_level',

            getVolume: function() {
                var volume = parseInt($.cookie(Cookie.cookieName), 10);

                if (isFinite(volume)) {
                    volume = Math.max(volume, this.min);
                    volume = Math.min(volume, this.max);
                } else {
                    volume = this.max;
                }

                return volume;
            },

            setVolume: function(value) {
                $.cookie(Cookie.cookieName, value, {
                    expires: 3650,
                    path: '/'
                });
            }
        };

        return VolumeControl;
    });
}(RequireJS.define));
