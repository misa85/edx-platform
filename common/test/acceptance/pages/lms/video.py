"""
Video player in the courseware.
"""

import time
import requests
from selenium.webdriver.common.action_chains import ActionChains
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, Promise
from bok_choy.javascript import wait_for_js, js_defined


VIDEO_BUTTONS = {
    'CC': '.hide-subtitles',
    'volume': '.volume',
    'play': '.video_control.play',
    'pause': '.video_control.pause',
    'fullscreen': '.add-fullscreen',
    'download_transcript': '.video-tracks > a',
    'speed': '.speeds'
}

CSS_CLASS_NAMES = {
    'closed_captions': '.closed .subtitles',
    'captions_rendered': '.video.is-captions-rendered',
    'captions': '.subtitles',
    'captions_text': '.subtitles > li',
    'error_message': '.video .video-player h3',
    'video_container': 'div.video',
    'video_sources': '.video-player video source',
    'video_spinner': '.video-wrapper .spinner',
    'video_xmodule': '.xmodule_VideoModule',
    'video_init': '.is-initialized',
    'video_time': 'div.vidtime',
    'video_display_name': '.vert h2'
}

VIDEO_MODES = {
    'html5': 'div.video video',
    'youtube': 'div.video iframe'
}

VIDEO_MENUS = {
    'language': '.lang .menu',
    'speed': '.speed .menu',
    'download_transcript': '.video-tracks .a11y-menu-list',
    'transcript-format': '.video-tracks .a11y-menu-button'
}


@js_defined('window.Video', 'window.RequireJS.require', 'window.jQuery')
class VideoPage(PageObject):
    """
    Video player in the courseware.
    """

    url = None

    @wait_for_js
    def is_browser_on_page(self):
        return self.q(css='div{0}'.format(CSS_CLASS_NAMES['video_xmodule'])).present

    @wait_for_js
    # TODO(muhammad-ammar) Move this function to somewhere else so that others can use it also. # pylint: disable=W0511
    def _wait_for_element(self, element_selector, promise_desc):
        """
        Wait for element specified by `element_selector` is present in DOM.
        :param element_selector: css selector of the element
        :param promise_desc: Description of the Promise, used in log messages.
        :return: BrokenPromise: the `Promise` was not satisfied within the time or attempt limits.
        """
        def _is_element_present():
            """
            Check if web-element present in DOM
            :return: bool
            """
            return self.q(css=element_selector).present

        EmptyPromise(_is_element_present, promise_desc, timeout=200).fulfill()

    @wait_for_js
    def wait_for_video_class(self):
        """
        Wait until element with class name `video` appeared in DOM.
        """
        self.wait_for_ajax()

        video_selector = '{0}'.format(CSS_CLASS_NAMES['video_container'])
        self._wait_for_element(video_selector, 'Video is initialized')

    @wait_for_js
    def wait_for_video_player_render(self):
        """
        Wait until Video Player Rendered Completely.
        """
        self.wait_for_video_class()
        self._wait_for_element(CSS_CLASS_NAMES['video_init'], 'Video Player Initialized')
        self._wait_for_element(CSS_CLASS_NAMES['video_time'], 'Video Player Initialized')

        def _is_finished_loading():
            """
            Check if video loading completed
            :return: bool
            """
            return not self.q(css=CSS_CLASS_NAMES['video_spinner']).visible

        EmptyPromise(_is_finished_loading, 'Finished loading the video', timeout=200).fulfill()

        self.wait_for_ajax()

    def get_video_vertical_selector(self, video_display_name=None):
        """
        Get selector for a video vertical.
        :param video_display_name: str
        """
        if video_display_name:
            video_display_names = self.q(css=CSS_CLASS_NAMES['video_display_name']).text
            if video_display_name not in video_display_names:
                raise ValueError("Incorrect Video Display Name: '{0}'".format(video_display_name))
            return '.vert.vert-{}'.format(video_display_names.index(video_display_name))
        else:
            return '.vert.vert-0'

    def get_element_selector(self, video_display_name, class_name):
        """
        Construct unique element selector
        :param video_display_name: str
        :param class_name: str
        :return: str
        """
        return '{vertical} {video_element}'.format(
            vertical=self.get_video_vertical_selector(video_display_name),
            video_element=class_name)

    def is_video_rendered(self, mode, video_display_name=None):
        """
        Check that if video is rendered in `mode`.
        :param mode: Video mode, `html5` or `youtube`
        :param video_display_name: str
        """
        selector = self.get_element_selector(video_display_name, VIDEO_MODES[mode])

        def _is_element_present():
            """
            Check if a web element is present in DOM
            :return:
            """
            is_present = self.q(css=selector).present
            return is_present, is_present

        return Promise(_is_element_present, 'Video Rendering Failed in {0} mode.'.format(mode)).fulfill()

    @property
    def is_autoplay_enabled(self, video_display_name=None):
        """
        Extract `data-autoplay` attribute to check video autoplay is enabled or disabled.
        :param video_display_name: str
        """
        selector = self.get_element_selector(video_display_name, CSS_CLASS_NAMES['video_container'])
        auto_play = self.q(css=selector).attrs('data-autoplay')[0]

        if auto_play.lower() == 'false':
            return False

        return True

    @property
    def is_error_message_shown(self, video_display_name=None):
        """
        Checks if video player error message shown.
        :param video_display_name: str
        :return: bool
        """
        selector = self.get_element_selector(video_display_name, CSS_CLASS_NAMES['error_message'])
        return self.q(css=selector).visible

    @property
    def error_message_text(self, video_display_name=None):
        """
        Extract video player error message text.
        :param video_display_name: str
        :return: str
        """
        selector = self.get_element_selector(video_display_name, CSS_CLASS_NAMES['error_message'])
        return self.q(css=selector).text[0]

    def is_button_shown(self, button_id, video_display_name=None):
        """
        Check if a video button specified by `button_id` is visible
        :param button_id: button css selector
        :param video_display_name: str
        :return: bool
        """
        selector = self.get_element_selector(video_display_name, VIDEO_BUTTONS[button_id])
        return self.q(css=selector).visible

    @wait_for_js
    def show_captions(self, video_display_name=None):
        """
        Show the video captions.
        :param video_display_name: str
        """
        subtitle_selector = self.get_element_selector(video_display_name, CSS_CLASS_NAMES['closed_captions'])

        def _is_subtitles_open():
            """
            Check if subtitles are opened
            :return: bool
            """
            is_open = not self.q(css=subtitle_selector).present
            return is_open

        # Make sure that the CC button is there
        EmptyPromise(lambda: self.is_button_shown('CC', video_display_name),
                     "CC button is shown").fulfill()

        # Check if the captions are already open and click if not
        if _is_subtitles_open() is False:
            self.click_player_button('CC', video_display_name)

        # Verify that they are now open
        EmptyPromise(_is_subtitles_open,
                     "Subtitles are shown").fulfill()

    @property
    def captions_text(self, video_display_name=None):
        """
        Extract captions text.
        :param video_display_name: str
        :return: str
        """
        # wait until captions rendered completely
        captions_rendered_selector = self.get_element_selector(video_display_name, CSS_CLASS_NAMES['captions_rendered'])
        self._wait_for_element(captions_rendered_selector, 'Captions Rendered')

        captions_selector = self.get_element_selector(video_display_name, CSS_CLASS_NAMES['captions_text'])
        subs = self.q(css=captions_selector).html

        return ' '.join(subs)

    def set_speed(self, speed, video_display_name=None):
        """
        Change the video play speed.
        :param speed: speed value in str
        :param video_display_name: str
        """
        # mouse over to video speed button
        speed_menu_selector = self.get_element_selector(video_display_name, VIDEO_BUTTONS['speed'])
        element_to_hover_over = self.q(css=speed_menu_selector).results[0]
        hover = ActionChains(self.browser).move_to_element(element_to_hover_over)
        hover.perform()

        speed_selector = self.get_element_selector(video_display_name, 'li[data-speed="{speed}"] a'.format(speed=speed))
        self.q(css=speed_selector).first.click()

    def click_player_button(self, button, video_display_name=None):
        """
        Click on `button`.
        :param button: key in VIDEO_BUTTONS dictionary, its value will give us the css selector for `button`
        :param video_display_name: str
        """
        button_selector = self.get_element_selector(video_display_name, VIDEO_BUTTONS[button])
        self.q(css=button_selector).first.click()

        if button == 'play':
            # wait for video buffering
            self._wait_for_video_play(video_display_name)

        self.wait_for_ajax()

    def _wait_for_video_play(self, video_display_name=None):
        """
        Wait until video starts playing
        :param video_display_name: str
        :return: BrokenPromise
        """
        playing_selector = self.get_element_selector(video_display_name, CSS_CLASS_NAMES['video_container'])
        pause_selector = self.get_element_selector(video_display_name, VIDEO_BUTTONS['pause'])

        def _check_promise():
            """
            Promise check
            :return: bool
            """
            return 'is-playing' in self.q(css=playing_selector).attrs('class')[0] and self.q(css=pause_selector).present

        EmptyPromise(_check_promise, 'Video is Playing', timeout=200).fulfill()

    def _get_element_dimensions(self, selector):
        """
        Gets the width and height of element specified by `selector`
        :param selector: str, css selector of a web element
        :return: dict
        """
        element = self.q(css=selector).results[0]
        return element.size

    def _get_dimensions(self, video_display_name=None):
        """
        Gets the video player dimensions
        :param video_display_name: str
        :return: tuple
        """
        iframe_selector = self.get_element_selector(video_display_name, '.video-player iframe,')
        video_selector = self.get_element_selector(video_display_name, ' .video-player video')
        video = self._get_element_dimensions(iframe_selector + video_selector)
        wrapper = self._get_element_dimensions(self.get_element_selector(video_display_name, '.tc-wrapper'))
        controls = self._get_element_dimensions(self.get_element_selector(video_display_name, '.video-controls'))
        progress_slider = self._get_element_dimensions(
            self.get_element_selector(video_display_name, '.video-controls > .slider'))

        expected = dict(wrapper)
        expected['height'] -= controls['height'] + 0.5 * progress_slider['height']

        return video, expected

    def is_aligned(self, is_transcript_visible, video_display_name=None):
        """
        Check if video is aligned properly.
        :param is_transcript_visible: bool
        :param video_display_name: str
        :return: bool
        """
        # Width of the video container in css equal 75% of window if transcript enabled
        wrapper_width = 75 if is_transcript_visible else 100
        initial = self.browser.get_window_size()

        self.browser.set_window_size(300, 600)

        # Wait for browser to resize completely
        # Currently there is no other way to wait instead of explicit wait
        time.sleep(0.2)

        real, expected = self._get_dimensions(video_display_name)

        width = round(100 * real['width'] / expected['width']) == wrapper_width

        self.browser.set_window_size(600, 300)

        # Wait for browser to resize completely
        # Currently there is no other way to wait instead of explicit wait
        time.sleep(0.2)

        real, expected = self._get_dimensions(video_display_name)

        height = abs(expected['height'] - real['height']) <= 5

        # Restore initial window size
        self.browser.set_window_size(
            initial['width'], initial['height']
        )

        return all([width, height])

    def _get_transcript(self, url):
        """
        Sends a http get request.
        """
        kwargs = dict()

        session_id = [{i['name']: i['value']} for i in self.browser.get_cookies() if i['name'] == u'sessionid']
        if session_id:
            kwargs.update({
                'cookies': session_id[0]
            })

        response = requests.get(url, **kwargs)
        return response.status_code < 400, response.headers, response.content

    def downloaded_transcript_contains_text(self, transcript_format, text_to_search, video_display_name=None):
        """
        Download the transcript in format `transcript_format` and check that it contains the text `text_to_search`
        :param transcript_format: `srt` or `txt`
        :param text_to_search: str
        :param video_display_name: str
        :return: bool
        """
        transcript_selector = self.get_element_selector(video_display_name, VIDEO_MENUS['transcript-format'])

        # check if we have a transcript with correct format
        if '.' + transcript_format not in self.q(css=transcript_selector).text[0]:
            return False

        formats = {
            'srt': 'application/x-subrip',
            'txt': 'text/plain',
        }

        transcript_url_selector = self.get_element_selector(video_display_name, VIDEO_BUTTONS['download_transcript'])
        url = self.q(css=transcript_url_selector).attrs('href')[0]
        result, headers, content = self._get_transcript(url)

        if result is False:
            return False

        if formats[transcript_format] not in headers.get('content-type', ''):
            return False

        if text_to_search not in content.decode('utf-8'):
            return False

        return True

    def select_language(self, code, video_display_name=None):
        """
        Select captions for language `code`
        :param code: str, two character language code like `en`, `zh`
        :param video_display_name: str
        :return: bool, True for Success, False for Failure or BrokenPromise
        """
        self.wait_for_ajax()

        # mouse over to CC button
        cc_button_selector = self.get_element_selector(video_display_name, VIDEO_BUTTONS["CC"])
        element_to_hover_over = self.q(css=cc_button_selector).results[0]
        hover = ActionChains(self.browser).move_to_element(element_to_hover_over)
        hover.perform()

        language_selector = VIDEO_MENUS["language"] + ' li[data-lang-code="{code}"]'.format(code=code)
        language_selector = self.get_element_selector(video_display_name, language_selector)
        self.q(css=language_selector).first.click()

        if 'is-active' != self.q(css=language_selector).attrs('class')[0]:
            return False

        active_lang_selector = self.get_element_selector(video_display_name, VIDEO_MENUS["language"] + ' li.is-active')
        if len(self.q(css=active_lang_selector).results) != 1:
            return False

        # Make sure that all ajax requests that affects the display of captions are finished.
        # For example, request to get new translation etc.
        self.wait_for_ajax()

        captions_selector = self.get_element_selector(video_display_name, CSS_CLASS_NAMES['captions'])
        EmptyPromise(lambda: self.q(css=captions_selector).visible, 'Subtitles Visible').fulfill()

        # wait until captions rendered completely
        captions_rendered_selector = self.get_element_selector(video_display_name, CSS_CLASS_NAMES['captions_rendered'])
        self._wait_for_element(captions_rendered_selector, 'Captions Rendered')

        return True

    def is_menu_exist(self, menu_name, video_display_name=None):
        """
        Check if menu `menu_name` exists
        :param menu_name: menu name
        :param video_display_name: str
        :return: bool
        """
        selector = self.get_element_selector(video_display_name, VIDEO_MENUS[menu_name])
        return self.q(css=selector).present

    def select_transcript_format(self, transcript_format, video_display_name=None):
        """
        Select transcript with format `transcript_format`
        :param transcript_format: `srt` or `txt`
        :param video_display_name: str
        :return: bool
        """
        button_selector = self.get_element_selector(video_display_name, VIDEO_MENUS['transcript-format'])

        button = self.q(css=button_selector).results[0]

        coord_y = button.location_once_scrolled_into_view['y']
        self.browser.execute_script("window.scrollTo(0, {});".format(coord_y))

        hover = ActionChains(self.browser).move_to_element(button)
        hover.perform()

        if '...' not in self.q(css=button_selector).text[0]:
            return False

        menu_selector = self.get_element_selector(video_display_name, VIDEO_MENUS['download_transcript'])
        menu_items = self.q(css=menu_selector + ' a').results
        for item in menu_items:
            if item.get_attribute('data-value') == transcript_format:
                item.click()
                self.wait_for_ajax()
                break

        self.browser.execute_script("window.scrollTo(0, 0);")

        if self.q(css=menu_selector + ' .active a').attrs('data-value')[0] != transcript_format:
            return False

        if '.' + transcript_format not in self.q(css=button_selector).text[0]:
            return False

        return True
