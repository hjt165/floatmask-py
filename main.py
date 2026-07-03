# FloatMask 主界面
# Kivy App + ScreenManager
# 对应原 Java 项目 com.floatmask.activities.MainActivity.java

import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock

import constants
import preferences
import permissions
from overlay import FloatingOverlay
from gesture_handler import GestureHandler
from edge_snap import EdgeSnapHelper


class MainScreen(Screen):
    """主控制界面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # 标题
        title = Label(
            text="智能字幕遮挡",
            font_size=24,
            size_hint_y=0.1
        )
        self.layout.add_widget(title)

        # 悬浮窗开关
        switch_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        switch_layout.add_widget(Label(text="悬浮窗开关", size_hint_x=0.6))
        self.toggle_switch = Switch(active=False, size_hint_x=0.4)
        self.toggle_switch.bind(active=self.on_toggle)
        switch_layout.add_widget(self.toggle_switch)
        self.layout.add_widget(switch_layout)

        # 边缘吸附开关
        snap_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        snap_layout.add_widget(Label(text="边缘吸附", size_hint_x=0.6))
        self.snap_switch = Switch(active=True, size_hint_x=0.4)
        snap_layout.add_widget(self.snap_switch)
        self.layout.add_widget(snap_layout)

        # 颜色选择
        color_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        color_layout.add_widget(Label(text="遮挡颜色", size_hint_x=0.6))
        self.color_spinner = Spinner(
            text='灰色半透明',
            values=('灰色半透明', '黑色半透明', '纯黑'),
            size_hint_x=0.4
        )
        self.color_spinner.bind(text=self.on_color_change)
        color_layout.add_widget(self.color_spinner)
        self.layout.add_widget(color_layout)

        # 权限按钮
        self.perm_btn = Button(
            text="授予悬浮窗权限",
            size_hint_y=0.1
        )
        self.perm_btn.bind(on_press=self.on_request_permission)
        self.layout.add_widget(self.perm_btn)

        # 自启动按钮
        self.autostart_btn = Button(
            text="开启自启动",
            size_hint_y=0.1
        )
        self.autostart_btn.bind(on_press=self.on_autostart)
        self.layout.add_widget(self.autostart_btn)

        # 电池优化按钮
        self.battery_btn = Button(
            text="忽略电池优化",
            size_hint_y=0.1
        )
        self.battery_btn.bind(on_press=self.on_battery_opt)
        self.layout.add_widget(self.battery_btn)

        # 状态标签
        self.status_label = Label(
            text="状态：未启动",
            font_size=14,
            size_hint_y=0.1
        )
        self.layout.add_widget(self.status_label)

        self.add_widget(self.layout)

        # Overlay 和手势处理器
        self.overlay = None
        self.gesture_handler = None
        self.edge_snap = None

        # 启动时检查权限
        Clock.schedule_once(self._check_permissions, 0.5)

    def _check_permissions(self, dt):
        """启动时检查权限状态"""
        if platform == 'android':
            if permissions.has_overlay_permission():
                self.status_label.text = "状态：已授予悬浮窗权限"
                self.perm_btn.text = "悬浮窗权限 ✓"
            else:
                self.status_label.text = "状态：需要授予悬浮窗权限"

    def on_toggle(self, instance, value):
        """悬浮窗开关"""
        if value:
            self._start_overlay()
        else:
            self._stop_overlay()

    def _start_overlay(self):
        """启动悬浮窗"""
        if self.overlay is not None:
            return

        if platform == 'android' and not permissions.has_overlay_permission():
            permissions.request_overlay_permission()
            self.toggle_switch.active = False
            return

        # 创建悬浮窗
        self.overlay = FloatingOverlay()
        Window.add_widget(self.overlay)

        # 创建手势处理器
        self.gesture_handler = GestureHandler(
            self.overlay,
            on_color_change=self._on_color_changed,
            on_alpha_change=self._on_alpha_changed,
            on_size_change=self._on_size_changed,
            on_double_tap=self._on_double_tap
        )

        # 创建边缘吸附
        self.edge_snap = EdgeSnapHelper(
            self.overlay,
            enabled=self.snap_switch.active
        )

        # 加载保存的状态
        if preferences.has_saved_state():
            state = preferences.load_state()
            self.overlay.set_position(state['x'], state['y'])
            self.overlay.set_size(state['width'], state['height'])
            self.overlay.set_alpha(state['alpha'])
            # 设置颜色
            for i, c in enumerate(constants.COLORS):
                if c == state['color']:
                    self.gesture_handler.set_color_index(i)
                    self.overlay.set_color(c)
                    break

        # 绑定触摸事件
        Window.bind(on_touch_down=self._on_touch_down)
        Window.bind(on_touch_move=self._on_touch_move)
        Window.bind(on_touch_up=self._on_touch_up)

        self.status_label.text = "状态：悬浮窗已启动"
        preferences.save_service_enabled(True)

    def _stop_overlay(self):
        """停止悬浮窗"""
        if self.overlay is None:
            return

        # 保存状态
        x, y = self.overlay.get_position()
        w, h = self.overlay.get_size()
        color_idx = self.gesture_handler._color_index
        preferences.save_all_state(
            x, y, w, h,
            constants.COLORS[color_idx],
            self.overlay.floating_alpha
        )

        # 移除悬浮窗
        Window.remove_widget(self.overlay)
        self.overlay = None
        self.gesture_handler = None
        self.edge_snap = None

        Window.unbind(on_touch_down=self._on_touch_down)
        Window.unbind(on_touch_move=self._on_touch_move)
        Window.unbind(on_touch_up=self._on_touch_up)

        self.status_label.text = "状态：已停止"
        preferences.save_service_enabled(False)

    def _on_touch_down(self, window, touch):
        if self.gesture_handler:
            return self.gesture_handler.on_touch_down(touch)

    def _on_touch_move(self, window, touch):
        if self.gesture_handler:
            return self.gesture_handler.on_touch_move(touch)

    def _on_touch_up(self, window, touch):
        if self.gesture_handler:
            result = self.gesture_handler.on_touch_up(touch)
            # 松手后触发边缘吸附
            if self.edge_snap and self.gesture_handler._gesture_state is None:
                self.edge_snap.snap_to_edge()
            return result

    def _on_color_changed(self, color_index):
        """颜色变化回调"""
        if self.overlay:
            self.overlay.set_color(constants.COLORS[color_index])

    def _on_alpha_changed(self, alpha):
        """透明度变化回调"""
        if self.overlay:
            self.overlay.set_alpha(alpha)

    def _on_size_changed(self, width, height):
        """尺寸变化回调"""
        pass

    def _on_double_tap(self):
        """双击回调"""
        pass

    def on_color_change(self, spinner, text):
        """颜色选择"""
        color_map = {
            '灰色半透明': constants.COLOR_TRANSPARENT_GRAY,
            '黑色半透明': constants.COLOR_TRANSPARENT_BLACK,
            '纯黑': constants.COLOR_SOLID_BLACK,
        }
        color = color_map.get(text, constants.COLOR_TRANSPARENT_GRAY)
        if self.overlay:
            idx = constants.COLORS.index(color) if color in constants.COLORS else 0
            self.gesture_handler.set_color_index(idx)
            self.overlay.set_color(color)
        preferences.save_default_color(color)

    def on_request_permission(self, instance):
        """请求悬浮窗权限"""
        permissions.request_overlay_permission()

    def on_autostart(self, instance):
        """打开自启动设置"""
        import keep_alive
        keep_alive.open_vendor_autostart()

    def on_battery_opt(self, instance):
        """请求忽略电池优化"""
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
        # 保存状态
        pass


if __name__ == '__main__':
    FloatMaskApp().run()
