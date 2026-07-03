# FloatMask 权限管理
# 通过 Pyjnius 调用 Android Settings API
# 对应原 Java 项目 com.floatmask.utils.PermissionUtils.java

from kivy.utils import platform
import constants


def has_overlay_permission():
    """检查悬浮窗权限是否已授予"""
    if platform != 'android':
        return True

    from jnius import autoclass
    Settings = autoclass('android.provider.Settings')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    return Settings.canDrawOverlays(activity)


def request_overlay_permission():
    """请求悬浮窗权限，跳转到系统设置页面"""
    if platform != 'android':
        return

    from jnius import autoclass
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity

    intent = Intent(
        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
        Uri.parse(f"package:{activity.getPackageName()}")
    )
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    activity.startActivity(intent)


def is_ignoring_battery_optimizations():
    """检查是否已忽略电池优化"""
    if platform != 'android':
        return True

    from jnius import autoclass
    PowerManager = autoclass('android.os.PowerManager')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    pm = activity.getSystemService(PowerManager.POWER_SERVICE)
    return pm.isIgnoringBatteryOptimizations(activity.getPackageName())


def request_ignore_battery_optimizations():
    """请求忽略电池优化"""
    if platform != 'android':
        return

    from jnius import autoclass
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity

    intent = Intent(
        android.provider.Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
        Uri.parse(f"package:{activity.getPackageName()}")
    )
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    activity.startActivity(intent)
