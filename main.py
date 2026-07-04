# FloatMask 主界面
# 使用系统级 WindowManager 悬浮窗
# 对应原 Java 项目 com.floatmask.activities.MainActivity.java

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.utils import platform
from kivy.clock import Clock

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'simhei.ttf')
FONT_NAME = 'Chinese'
if os.path.exists(FONT_PATH):
    LabelBase.register(name=FONT_NAME, fn_regular=FONT_PATH)

from kivy.lang import Builder
Builder.load_string(f'''
<SpinnerOption>:
    font_name: '{FONT_NAME}'
''')

import constants
import preferences
import permissions
from native_overlay import NativeOverlay


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        title = Label(
            text="智能字幕遮挡",
            font_size=24,
            font_name=FONT_NAME,
            size_hint_y=0.1
        )
        self.layout.add_widget(title)

        switch_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        switch_layout.add_widget(Label(text="悬浮窗开关", font_name=FONT_NAME, size_hint_x=0.6))
        self.toggle_switch = Switch(active=False, size_hint_x=0.4)
        self.toggle_switch.bind(active=self.on_toggle)
        switch_layout.add_widget(self.toggle_switch)
        self.layout.add_widget(switch_layout)

        snap_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        snap_layout.add_widget(Label(text="边缘吸附", font_name=FONT_NAME, size_hint_x=0.6))
        self.snap_switch = Switch(active=True, size_hint_x=0.4)
        self.snap_switch.bind(active=self.on_snap_toggle)
        snap_layout.add_widget(self.snap_switch)
        self.layout.add_widget(snap_layout)

        color_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        color_layout.add_widget(Label(text="遮挡颜色", font_name=FONT_NAME, size_hint_x=0.6))
        self.color_spinner = Spinner(
            text='灰色半透明',
            values=('灰色半透明', '黑色半透明', '纯黑'),
            font_name=FONT_NAME,
            size_hint_x=0.4
        )
        self.color_spinner.bind(text=self.on_color_change)
        color_layout.add_widget(self.color_spinner)
        self.layout.add_widget(color_layout)

        self.perm_btn = Button(
            text="授予悬浮窗权限",
            font_name=FONT_NAME,
            size_hint_y=0.1
        )
        self.perm_btn.bind(on_press=self.on_request_permission)
        self.layout.add_widget(self.perm_btn)

        self.autostart_btn = Button(
            text="开启自启动",
            font_name=FONT_NAME,
            size_hint_y=0.1
        )
        self.autostart_btn.bind(on_press=self.on_autostart)
        self.layout.add_widget(self.autostart_btn)

        self.battery_btn = Button(
            text="忽略电池优化",
            font_name=FONT_NAME,
            size_hint_y=0.1
        )
        self.battery_btn.bind(on_press=self.on_battery_opt)
        self.layout.add_widget(self.battery_btn)

        self.status_label = Label(
            text="状态：未启动",
            font_size=14,
            font_name=FONT_NAME,
            size_hint_y=0.1
        )
        self.layout.add_widget(self.status_label)

        self.add_widget(self.layout)

        self.native_overlay = None
        self._color_index = 0
        self._snap_enabled = True
        self._snap_event = None

        Clock.schedule_once(self._check_permissions, 0.5)

    def _check_permissions(self, dt):
        if platform == 'android':
            if permissions.has_overlay_permission():
                self.status_label.text = "状态：已授予悬浮窗权限"
                self.perm_btn.text = "悬浮窗权限 ✓"
            else:
                self.status_label.text = "状态：需要授予悬浮窗权限"

    def on_toggle(self, instance, value):
        if value:
            self._start_overlay()
        else:
            self._stop_overlay()

    def _start_overlay(self):
        if self.native_overlay is not None:
            return

        if platform == 'android' and not permissions.has_overlay_permission():
            permissions.request_overlay_permission()
            self.toggle_switch.active = False
            return

        self.native_overlay = NativeOverlay()

        x, y, w, h = 100, 100, constants.DEFAULT_FLOATING_WIDTH, constants.DEFAULT_FLOATING_HEIGHT
        if preferences.has_saved_state():
            state = preferences.load_state()
            x, y = state['x'], state['y']
            w, h = state['width'], state['height']
            self._color_index = 0
            for i, c in enumerate(constants.COLORS):
                if c == state['color']:
                    self._color_index = i
                    break

        color = constants.COLORS[self._color_index]
        self.native_overlay.show(x, y, w, h, color)

        self.native_overlay.start_polling(
            on_color_change=self._on_native_color_change,
            on_double_tap=self._on_native_double_tap
        )

        self.status_label.text = "状态：悬浮窗已启动"
        preferences.save_service_enabled(True)

        if self._snap_enabled:
            self._start_snap_polling()

    def _stop_overlay(self):
        if self.native_overlay is None:
            return

        x, y = self.native_overlay.get_position()
        w, h = self.native_overlay.get_size()
        color = constants.COLORS[self._color_index]
        preferences.save_all_state(x, y, w, h, color, 1.0)

        self.native_overlay.stop_polling()
        self.native_overlay.hide()
        self.native_overlay = None

        self._stop_snap_polling()
        self.status_label.text = "状态：已停止"
        preferences.save_service_enabled(False)

    def _on_native_color_change(self, color_index):
        self._color_index = color_index
        self.native_overlay.set_color(constants.COLORS[color_index])

    def _on_native_double_tap(self):
        pass

    def on_color_change(self, spinner, text):
        color_map = {
            '灰色半透明': constants.COLOR_TRANSPARENT_GRAY,
            '黑色半透明': constants.COLOR_TRANSPARENT_BLACK,
            '纯黑': constants.COLOR_SOLID_BLACK,
        }
        color = color_map.get(text, constants.COLOR_TRANSPARENT_GRAY)
        if self.native_overlay:
            idx = constants.COLORS.index(color) if color in constants.COLORS else 0
            self._color_index = idx
            self.native_overlay.set_color(color)
        preferences.save_default_color(color)

    def on_snap_toggle(self, instance, value):
        self._snap_enabled = value
        preferences.save_edge_snap_enabled(value)
        if value and self.native_overlay:
            self._start_snap_polling()
        else:
            self._stop_snap_polling()

    def _start_snap_polling(self):
        self._stop_snap_polling()
        self._snap_event = Clock.schedule_interval(self._do_snap_poll, 1.0 / 30)

    def _stop_snap_polling(self):
        if self._snap_event:
            self._snap_event.cancel()
            self._snap_event = None

    def _do_snap_poll(self, dt):
        if self.native_overlay is None:
            return

        from jnius import autoclass
        OverlayView = autoclass('com.floatmask.OverlayView')
        action = OverlayView.touchAction

        if action == 2 or action == 4:
            OverlayView.touchAction = -1
            self._do_snap()

    def _do_snap(self):
        if self.native_overlay is None:
            return

        x, y = self.native_overlay.get_position()
        w, h = self.native_overlay.get_size()
        sw, sh = Window.width, Window.height
        threshold = constants.EDGE_SNAP_THRESHOLD

        target_x, target_y = x, y
        if x < threshold:
            target_x = constants.EDGE_SNAP_MARGIN
        elif x + w > sw - threshold:
            target_x = sw - w - constants.EDGE_SNAP_MARGIN
        if y + h > sh - threshold:
            target_y = sh - h - constants.EDGE_SNAP_MARGIN
        elif y < threshold:
            target_y = constants.EDGE_SNAP_MARGIN

        if target_x != x or target_y != y:
            self.native_overlay.set_position(target_x, target_y)


    def on_request_permission(self, instance):
        permissions.request_overlay_permission()

    def on_autostart(self, instance):
        import keep_alive
        keep_alive.open_vendor_autostart()

    def on_battery_opt(self, instance):
        import keep_alive
        keep_alive.open_battery_optimization()


class FloatMaskApp(App):
    def build(self):
        self.title = "智能字幕遮挡"
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

    def on_pause(self):
        return True

    def on_stop(self):
        pass


if __name__ == '__main__':
    FloatMaskApp().run()
