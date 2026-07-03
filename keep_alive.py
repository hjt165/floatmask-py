# FloatMask 保活机制
# 通过 Pyjnius 调用厂商自启动 Intent
# 对应原 Java 项目 com.floatmask.utils.KeepAliveManager.java

from kivy.utils import platform
import constants


# 各厂商自启动设置页面包名和类名
VENDOR_INTENTS = [
    # 华为
    {
        'package': 'com.huawei.systemmanager',
        'activity': 'com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity',
    },
    # 小米
    {
        'package': 'com.miui.securitycenter',
        'activity': 'com.miui.permcenter.autostart.AutoStartManagementActivity',
    },
    # OPPO
    {
        'package': 'com.coloros.safecenter',
        'activity': 'com.coloros.safecenter.startupapp.StartupAppListActivity',
    },
    # VIVO
    {
        'package': 'com.vivo.permissionmanager',
        'activity': 'com.vivo.permissionmanager.activity.BgStartUpManagerActivity',
    },
    # 三星
    {
        'package': 'com.samsung.android.lool',
        'activity': 'com.samsung.android.sm.battery.ui.usage.BatteryActivity',
    },
]


def open_vendor_autostart():
    """尝试打开厂商自启动设置页面"""
    if platform != 'android':
        return False

    from jnius import autoclass
    Intent = autoclass('android.content.Intent')
    ComponentName = autoclass('android.content.ComponentName')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    pm = activity.getPackageManager()

    for intent_info in VENDOR_INTENTS:
        try:
            component = ComponentName(intent_info['package'], intent_info['activity'])
            intent = Intent()
            intent.setComponent(component)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

            # 检查是否可以解析
            if pm.resolveActivity(intent, 0) is not None:
                activity.startActivity(intent)
                return True
        except Exception:
            continue

    return False


def open_battery_optimization():
    """请求忽略电池优化"""
    if platform != 'android':
        return

    from jnius import autoclass
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity

    intent = Intent(
        'android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS',
        Uri.parse(f"package:{activity.getPackageName()}")
    )
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    try:
        activity.startActivity(intent)
    except Exception:
        pass
