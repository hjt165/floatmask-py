# FloatMask 前台服务
# Buildozer 服务入口
# 对应原 Java 项目 com.floatmask.service.OverlayService.java

import os
import sys

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivy.utils import platform
from kivy.clock import Clock

import constants
import preferences
import notification_helper


class OverlayService:
    """悬浮窗前台服务（Buildozer 服务进程）"""

    def __init__(self):
        self._notification_created = False
        self._service = None

    def start(self, service):
        """服务启动"""
        self._service = service

        if platform == 'android':
            self._setup_android(service)

    def _setup_android(self, service):
        """Android 特定的初始化"""
        from jnius import autoclass

        # 创建通知渠道
        notification_helper.create_notification_channel()

        # 提升为前台服务
        notification_helper.start_foreground(service)
        self._notification_created = True

        # 设置为粘性服务（被杀死后自动重启）
        Service = autoclass('android.app.Service')
        service.startSticky()

    def on_start_command(self, service, flags, start_id):
        """处理服务启动命令"""
        if platform == 'android':
            from jnius import autoclass
            Service = autoclass('android.app.Service')
            return Service.START_STICKY
        return 0

    def on_destroy(self):
        """服务销毁"""
        pass


# 全局服务实例
_service_instance = None


def get_service():
    """获取服务实例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = OverlayService()
    return _service_instance


def start(service):
    """Buildozer 服务入口"""
    svc = get_service()
    svc.start(service)


def stop(service):
    """Buildozer 服务停止"""
    pass
