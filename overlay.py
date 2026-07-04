# FloatMask 悬浮窗 Canvas 绘制
# 对应原 Java 项目 com.floatmask.view.FloatingMaskView.java

from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.core.window import Window
import constants


class FloatingOverlay(Widget):
    """悬浮窗主体，使用 Kivy Canvas 绘制圆角矩形 + 图标"""

    # 可观察属性
    floating_color = ListProperty([1, 1, 1, 1])
    floating_alpha = NumericProperty(1.0)
    is_resizing = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 从 Window 获取屏幕尺寸
        self.screen_width = Window.width
        self.screen_height = Window.height

        # 默认悬浮框尺寸（屏幕比例）
        self.float_w = min(
            constants.DEFAULT_FLOATING_WIDTH,
            int(self.screen_width * constants.MAX_SIZE_RATIO)
        )
        self.float_h = min(
            constants.DEFAULT_FLOATING_HEIGHT,
            int(self.screen_height * constants.MAX_HEIGHT_RATIO)
        )

        # 初始位置：屏幕中央
        self.x_offset = (self.screen_width - self.float_w) // 2
        self.y_offset = (self.screen_height - self.float_h) // 2

        # 图标尺寸
        self.icon_size = 20
        self.icon_padding = 10

        # 绑定属性变化触发重绘（不绑定 pos/size，避免 Kivy Window _update_childsize 递归）
        self.bind(floating_color=self._update_rect)
        self.bind(floating_alpha=self._update_rect)

        # 初始绘制
        self._update_rect()

    def _hex_to_rgba(self, argb_hex):
        """将 ARGB hex 值转换为 [r, g, b, a] 范围 0-1"""
        a = ((argb_hex >> 24) & 0xFF) / 255.0
        r = ((argb_hex >> 16) & 0xFF) / 255.0
        g = ((argb_hex >> 8) & 0xFF) / 255.0
        b = (argb_hex & 0xFF) / 255.0
        return [r, g, b, a * self.floating_alpha]

    def set_color(self, argb_hex):
        """设置悬浮框颜色"""
        self.floating_color = self._hex_to_rgba(argb_hex)

    def set_alpha(self, alpha):
        """设置整体透明度"""
        self.floating_alpha = alpha
        self._update_rect()

    def _update_rect(self, *args):
        """重绘 Canvas — uses x_offset/y_offset/float_w/float_h directly,
        avoids setting self.pos/self.size which triggers Kivy Window recursion."""
        self.canvas.clear()

        # Compute pos/size from our own fields (don't assign to self.pos/self.size)
        px, py = self.x_offset, self.y_offset
        pw, ph = self.float_w, self.float_h

        with self.canvas:
            # 圆角矩形背景
            Color(*self.floating_color)
            RoundedRectangle(
                pos=(px, py),
                size=(pw, ph),
                radius=[15, 15, 15, 15]
            )

            # 边框
            Color(0.5, 0.5, 0.5, 0.5 * self.floating_alpha)
            Line(
                rounded_rectangle=(px, py, pw, ph, 15),
                width=1
            )

    def set_position(self, x, y):
        """设置悬浮框位置"""
        self.x_offset = int(x)
        self.y_offset = int(y)
        self._update_rect()

    def get_position(self):
        """获取悬浮框位置"""
        return self.x_offset, self.y_offset

    def set_size(self, width, height):
        """设置悬浮框尺寸"""
        self.float_w = max(constants.MIN_FLOATING_SIZE, int(width))
        self.float_h = max(constants.MIN_FLOATING_SIZE, int(height))
        self._update_rect()

    def get_size(self):
        """获取悬浮框尺寸"""
        return self.float_w, self.float_h

    def get_icon_rect(self):
        """获取图标绘制区域（右下角）"""
        icon_x = self.x_offset + self.float_w - self.icon_size - self.icon_padding
        icon_y = self.y_offset + self.icon_padding
        return icon_x, icon_y, self.icon_size, self.icon_size

    def is_point_inside(self, x, y):
        """检查点是否在悬浮框内"""
        return (self.x_offset <= x <= self.x_offset + self.float_w and
                self.y_offset <= y <= self.y_offset + self.float_h)

    def is_in_resize_area(self, x, y):
        """检查点是否在缩放区域内（80px 角落区域）"""
        sx, sy = self.x_offset, self.y_offset
        sw, sh = self.float_w, self.float_h
        area = constants.RESIZE_AREA_SIZE

        # 四个角落的缩放区域
        in_left = (sx <= x <= sx + area)
        in_right = (sx + sw - area <= x <= sx + sw)
        in_bottom = (sy <= y <= sy + area)
        in_top = (sy + sh - area <= y <= sy + sh)

        return (in_left or in_right) and (in_top or in_bottom)
