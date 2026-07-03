# FloatMask 通知辅助
# 通过 Pyjnius 调用 Android NotificationManager
# 对应原 Java 项目 com.floatmask.utils.NotificationHelper.java

from kivy.utils import platform
import constants


def create_notification_channel():
    """创建通知渠道（Android 8.0+）"""
    if platform != 'android':
        return

    from jnius import autoclass
    NotificationChannel = autoclass('android.app.NotificationChannel')
    NotificationManager = autoclass('android.app.NotificationManager')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity

    channel = NotificationChannel(
        constants.NOTIFICATION_CHANNEL_ID,
        constants.NOTIFICATION_CHANNEL_NAME,
        NotificationManager.IMPORTANCE_LOW
    )
    channel.setDescription("悬浮窗服务运行中")
    channel.setShowBadge(False)

    manager = activity.getSystemService(NotificationManager)
    manager.createNotificationChannel(channel)


def build_notification():
    """构建前台服务通知"""
    if platform != 'android':
        return None

    from jnius import autoclass
    NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    R = autoclass('android.R')
    activity = PythonActivity.mActivity

    builder = NotificationCompat.Builder(activity, constants.NOTIFICATION_CHANNEL_ID)
    builder.setContentTitle("智能字幕遮挡")
    builder.setContentText("悬浮窗运行中")
    builder.setSmallIcon(R.drawable.ic_menu_info_details)
    builder.setPriority(NotificationCompat.PRIORITY_LOW)
    builder.setOngoing(True)

    return builder.build()


def start_foreground(service, notification_id=None):
    """将服务提升为前台服务"""
    if notification_id is None:
        notification_id = constants.NOTIFICATION_ID

    service.startForeground(notification_id, build_notification())


def stop_foreground(service):
    """停止前台服务"""
    service.stopForeground(True)
