# FloatMask 边缘吸附
# 对应原 Java 项目 com.floatmask.utils.EdgeSnapHelper.java

from kivy.clock import Clock
import constants


class EdgeSnapHelper:
    """边缘吸附逻辑，松手后自动吸附到最近的屏幕边缘"""

    def __init__(self, overlay, enabled=True):
        self.overlay = overlay
        self.enabled = enabled
        self._anim_event = None

    def snap_to_edge(self):
        """松手后调用，判断是否需要吸附并执行动画"""
        if not self.enabled:
            return

        if self._anim_event is not None:
            self._anim_event.cancel()
            self._anim_event = None

        x, y = self.overlay.get_position()
        w, h = self.overlay.get_size()
        sw = self.overlay.screen_width
        sh = self.overlay.screen_height
        threshold = constants.EDGE_SNAP_THRESHOLD
        margin = constants.EDGE_SNAP_MARGIN

        # 计算最近的吸附目标位置
        target_x, target_y = x, y

        # 左边缘吸附
        if x < threshold:
            target_x = margin
        # 右边缘吸附
        elif x + w > sw - threshold:
            target_x = sw - w - margin

        # 上边缘吸附
        if y + h > sh - threshold:
            target_y = sh - h - margin
        # 下边缘吸附
        elif y < threshold:
            target_y = margin

        # 如果需要吸附，执行动画
        if target_x != x or target_y != y:
            self._animate_to(target_x, target_y)
        else:
            # 超出边界时强制回弹
            target_x = max(-w * constants.MIN_VISIBLE_RATIO,
                           min(sw - w * (1 - constants.MIN_VISIBLE_RATIO), target_x))
            target_y = max(-h * constants.MIN_VISIBLE_RATIO,
                           min(sh - h * (1 - constants.MIN_VISIBLE_RATIO), target_y))
            if target_x != x or target_y != y:
                self._animate_to(target_x, target_y)

    def _animate_to(self, target_x, target_y):
        """简单的线性插值动画"""
        start_x, start_y = self.overlay.get_position()
        duration = constants.EDGE_SNAP_ANIMATION_DURATION
        steps = max(1, int(duration * 60))  # 60fps
        dx = (target_x - start_x) / steps
        dy = (target_y - start_y) / steps
        self._anim_step = 0
        self._anim_steps = steps
        self._anim_dx = dx
        self._anim_dy = dy
        self._anim_target = (target_x, target_y)

        if self._anim_event is not None:
            self._anim_event.cancel()

        self._anim_event = Clock.schedule_interval(self._do_anim_step, 1.0 / 60)

    def _do_anim_step(self, dt):
        """动画步进"""
        self._anim_step += 1
        x, y = self.overlay.get_position()
        nx = x + self._anim_dx
        ny = y + self._anim_dy

        if self._anim_step >= self._anim_steps:
            nx, ny = self._anim_target
            self.overlay.set_position(nx, ny)
            if self._anim_event is not None:
                self._anim_event.cancel()
                self._anim_event = None
        else:
            self.overlay.set_position(nx, ny)

    def set_enabled(self, enabled):
        """启用/禁用边缘吸附"""
        self.enabled = enabled
