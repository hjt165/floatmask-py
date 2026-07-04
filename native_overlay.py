# FloatMask 原生系统悬浮窗
# 使用 WindowManager.addView() + OverlayView.java
# 实现真正的系统级悬浮窗，可以浮在其他应用上方

from kivy.utils import platform
from kivy.clock import Clock
import constants


def _to_signed32(val):
    val = val & 0xFFFFFFFF
    if val >= 0x80000000:
        val -= 0x100000000
    return val


class NativeOverlay:
    """原生悬浮窗包装器，通过 Pyjnius 调用 OverlayView.java"""

    def __init__(self):
        self._view = None
        self._color_index = 0
        self._current_alpha = 1.0
        self._poll_event = None
        self._on_color_change = None
        self._on_alpha_change = None
        self._on_double_tap = None
        self._last_touch_action = -1

    def show(self, x=100, y=100, w=None, h=None, color=None):
        """显示悬浮窗"""
        if platform != 'android':
            print("[NativeOverlay] Not on Android, skipping")
            return False

        from jnius import autoclass

        Context = autoclass('android.content.Context')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        OverlayView = autoclass('com.floatmask.OverlayView')

        self._view = OverlayView(activity)

        if w is None:
            w = constants.DEFAULT_FLOATING_WIDTH
        if h is None:
            h = constants.DEFAULT_FLOATING_HEIGHT
        if color is not None:
            self._view.setColor(_to_signed32(color))

        self._view.show(int(x), int(y), int(w), int(h))
        return True

    def hide(self):
        """隐藏悬浮窗"""
        if self._view is not None:
            self._view.hide()
            self._view = None
        if self._poll_event is not None:
            self._poll_event.cancel()
            self._poll_event = None

    def set_color(self, argb_hex):
        if self._view is not None:
            self._view.setColor(_to_signed32(argb_hex))

    def set_position(self, x, y):
        """设置位置"""
        if self._view is not None:
            self._view.moveTo(float(x), float(y))

    def set_size(self, w, h):
        """设置尺寸"""
        if self._view is not None:
            self._view.resizeTo(int(w), int(h))

    def set_alpha(self, alpha):
        """设置透明度"""
        if self._view is not None:
            self._view.setOverlayAlpha(float(alpha))

    def get_position(self):
        """获取位置"""
        if self._view is None:
            return 0, 0
        return self._view.getPosX(), self._view.getPosY()

    def get_size(self):
        """获取尺寸"""
        if self._view is None:
            return 0, 0
        return self._view.getOverlayWidth(), self._view.getOverlayHeight()

    def start_polling(self, on_color_change=None, on_alpha_change=None, on_double_tap=None):
        """开始轮询 Java 端的触摸事件"""
        self._on_color_change = on_color_change
        self._on_alpha_change = on_alpha_change
        self._on_double_tap = on_double_tap
        self._last_touch_action = -1
        self._poll_event = Clock.schedule_interval(self._poll_touch, 1.0 / 30)

    def stop_polling(self):
        """停止轮询"""
        if self._poll_event is not None:
            self._poll_event.cancel()
            self._poll_event = None

    def _poll_touch(self, dt):
        """轮询 Java 端的触摸状态"""
        if self._view is None:
            return

        from jnius import autoclass
        OverlayView = autoclass('com.floatmask.OverlayView')

        action = OverlayView.touchAction
        if action == self._last_touch_action:
            return

        self._last_touch_action = action

        if action == 0:  # ACTION_DOWN
            pass  # handled in Java

        elif action == 1:  # ACTION_MOVE
            # Java handles drag/resize directly
            pass

        elif action == 2:  # ACTION_UP
            # Check if it was a double-tap
            OverlayView.touchAction = -1  # reset
            self._last_touch_action = -1

        elif action == 3:  # DOUBLE_TAP
            # Toggle color
            self._color_index = (self._color_index + 1) % len(constants.COLORS)
            if self._on_color_change:
                self._on_color_change(self._color_index)
            if self._on_double_tap:
                self._on_double_tap()
            OverlayView.touchAction = -1
            self._last_touch_action = -1
