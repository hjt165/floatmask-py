# FloatMask 手势处理
# 处理拖拽、缩放、双击、垂直滑动（无长按菜单）
# 对应原 Java 项目 com.floatmask.utils.TouchHelper.java

import time
import constants


class GestureHandler:
    """手势处理器，负责识别和分发手势事件"""

    def __init__(self, overlay, on_color_change=None, on_alpha_change=None,
                 on_size_change=None, on_double_tap=None):
        """
        overlay: FloatingOverlay 实例
        on_color_change: 回调函数(color_index)
        on_alpha_change: 回调函数(alpha)
        on_size_change: 回调函数(new_width, new_height)
        on_double_tap: 回调函数()
        """
        self.overlay = overlay
        self.on_color_change = on_color_change
        self.on_alpha_change = on_alpha_change
        self.on_size_change = on_size_change
        self.on_double_tap = on_double_tap

        # 手势状态
        self._touch_start_time = 0
        self._touch_start_pos = (0, 0)
        self._last_tap_time = 0
        self._gesture_state = None  # 'drag', 'resize', 'slide'
        self._drag_offset = (0, 0)

        # 缩放相关
        self._resize_start_pos = (0, 0)
        self._resize_start_size = (0, 0)

        # 颜色和透明度
        self._color_index = 0
        self._current_alpha = 1.0

    def set_color_index(self, idx):
        self._color_index = idx % len(constants.COLORS)

    def on_touch_down(self, touch):
        """触摸按下事件"""
        ox, oy = self.overlay.get_position()
        w, h = self.overlay.get_size()

        # 检查触摸点是否在悬浮框内
        tx, ty = touch.x, touch.y
        if not (ox <= tx <= ox + w and oy <= ty <= oy + h):
            return False

        self._touch_start_time = time.time()
        self._touch_start_pos = (tx, ty)

        # 检查是否在缩放区域
        if self.overlay.is_in_resize_area(tx, ty):
            self._gesture_state = 'resize'
            self._resize_start_pos = (tx, ty)
            self._resize_start_size = (w, h)
            self.overlay.is_resizing = True
            return True

        # 默认进入拖拽状态
        self._gesture_state = 'drag'
        self._drag_offset = (tx - ox, ty - oy)
        return True

    def on_touch_move(self, touch):
        """触摸移动事件"""
        if self._gesture_state is None:
            return False

        tx, ty = touch.x, touch.y
        sx, sy = self._touch_start_pos
        dx = tx - sx
        dy = ty - sy

        if self._gesture_state == 'drag':
            # 拖拽：移动悬浮框
            new_x = tx - self._drag_offset[0]
            new_y = ty - self._drag_offset[1]

            # 边界限制
            sw = self.overlay.screen_width
            sh = self.overlay.screen_height
            w, h = self.overlay.get_size()
            new_x = max(-w * constants.MIN_VISIBLE_RATIO,
                        min(sw - w * (1 - constants.MIN_VISIBLE_RATIO), new_x))
            new_y = max(-h * constants.MIN_VISIBLE_RATIO,
                        min(sh - h * (1 - constants.MIN_VISIBLE_RATIO), new_y))

            self.overlay.set_position(new_x, new_y)

        elif self._gesture_state == 'resize':
            # 缩放：根据拖拽距离调整尺寸
            rx, ry = self._resize_start_pos
            rw, rh = self._resize_start_size
            delta_x = tx - rx
            delta_y = ry - ty  # 向上为正

            new_w = rw + delta_x
            new_h = rh + delta_y

            # 最小尺寸限制
            new_w = max(constants.MIN_FLOATING_SIZE, new_w)
            new_h = max(constants.MIN_FLOATING_SIZE, new_h)

            # 最大尺寸限制
            max_w = self.overlay.screen_width * constants.MAX_SIZE_RATIO
            max_h = self.overlay.screen_height * constants.MAX_HEIGHT_RATIO
            new_w = min(max_w, new_w)
            new_h = min(max_h, new_h)

            self.overlay.set_size(new_w, new_h)

            if self.on_size_change:
                self.on_size_change(new_w, new_h)

        elif self._gesture_state == 'slide':
            # 垂直滑动：调节透明度
            slide_dy = ty - self._touch_start_pos[1]
            screen_h = self.overlay.screen_height
            alpha_delta = -slide_dy / (screen_h * 0.5)
            new_alpha = max(0.1, min(1.0, self._current_alpha + alpha_delta))
            self.overlay.set_alpha(new_alpha)

            if self.on_alpha_change:
                self.on_alpha_change(new_alpha)

        return True

    def on_touch_up(self, touch):
        """触摸抬起事件"""
        if self._gesture_state is None:
            return False

        tx, ty = touch.x, touch.y
        sx, sy = self._touch_start_pos
        dx = tx - sx
        dy = ty - sy
        elapsed = time.time() - self._touch_start_time

        if self._gesture_state == 'drag':
            if elapsed < 0.3 and abs(dy) > constants.MIN_DRAG_DISTANCE * 3:
                # 短距离垂直滑动 → 切换透明度（只有在非缩放区域触发）
                if not self.overlay.is_in_resize_area(sx, sy):
                    self._gesture_state = 'slide'
                    self._touch_start_pos = (tx, ty)
                    self._current_alpha = self.overlay.floating_alpha
                    self.overlay.is_resizing = False
                    return True

            elif elapsed < constants.DOUBLE_TAP_TIMEOUT and abs(dx) < 5 and abs(dy) < 5:
                # 双击检测
                now = time.time()
                if now - self._last_tap_time < constants.DOUBLE_TAP_TIMEOUT:
                    # 双击 → 切换颜色
                    self._color_index = (self._color_index + 1) % len(constants.COLORS)
                    if self.on_color_change:
                        self.on_color_change(self._color_index)
                    if self.on_double_tap:
                        self.on_double_tap()
                    self._last_tap_time = 0
                else:
                    self._last_tap_time = now

        self._gesture_state = None
        self.overlay.is_resizing = False
        return True
