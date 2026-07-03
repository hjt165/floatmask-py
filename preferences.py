# FloatMask 状态持久化
# 通过 Pyjnius 调用 Android SharedPreferences
# 对应原 Java 项目 com.floatmask.utils.PreferenceUtils.java

from kivy.utils import platform
import constants

_prefs = None


def _get_prefs():
    """获取 SharedPreferences 实例（懒加载单例）"""
    global _prefs
    if _prefs is not None:
        return _prefs

    if platform != 'android':
        return None

    from jnius import autoclass
    Context = autoclass('android.content.Context')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    _prefs = activity.getSharedPreferences(constants.PREF_NAME, Context.MODE_PRIVATE)
    return _prefs


def save_all_state(x, y, width, height, color, alpha):
    """一次性保存所有悬浮框状态"""
    prefs = _get_prefs()
    if prefs is None:
        return
    editor = prefs.edit()
    editor.putInt(constants.PREF_KEY_X, int(x))
    editor.putInt(constants.PREF_KEY_Y, int(y))
    editor.putInt(constants.PREF_KEY_WIDTH, int(width))
    editor.putInt(constants.PREF_KEY_HEIGHT, int(height))
    editor.putInt(constants.PREF_KEY_COLOR, int(color))
    editor.putFloat(constants.PREF_KEY_ALPHA, float(alpha))
    editor.apply()


def load_state():
    """加载保存的状态，返回 dict"""
    prefs = _get_prefs()
    if prefs is None:
        return {
            'x': constants.DEFAULT_FLOATING_WIDTH // 2,
            'y': constants.DEFAULT_FLOATING_HEIGHT // 2,
            'width': constants.DEFAULT_FLOATING_WIDTH,
            'height': constants.DEFAULT_FLOATING_HEIGHT,
            'color': constants.COLOR_TRANSPARENT_GRAY,
            'alpha': 1.0,
        }
    return {
        'x': prefs.getInt(constants.PREF_KEY_X, constants.DEFAULT_FLOATING_WIDTH // 2),
        'y': prefs.getInt(constants.PREF_KEY_Y, constants.DEFAULT_FLOATING_HEIGHT // 2),
        'width': prefs.getInt(constants.PREF_KEY_WIDTH, constants.DEFAULT_FLOATING_WIDTH),
        'height': prefs.getInt(constants.PREF_KEY_HEIGHT, constants.DEFAULT_FLOATING_HEIGHT),
        'color': prefs.getInt(constants.PREF_KEY_COLOR, constants.COLOR_TRANSPARENT_GRAY),
        'alpha': prefs.getFloat(constants.PREF_KEY_ALPHA, 1.0),
    }


def has_saved_state():
    """检查是否有保存的状态"""
    prefs = _get_prefs()
    if prefs is None:
        return False
    return prefs.contains(constants.PREF_KEY_X)


def save_edge_snap_enabled(enabled):
    """保存边缘吸附开关"""
    prefs = _get_prefs()
    if prefs is None:
        return
    prefs.edit().putBoolean(constants.PREF_KEY_EDGE_SNAP, enabled).apply()


def is_edge_snap_enabled():
    """获取边缘吸附开关"""
    prefs = _get_prefs()
    if prefs is None:
        return True
    return prefs.getBoolean(constants.PREF_KEY_EDGE_SNAP, True)


def save_default_color(color):
    """保存默认颜色"""
    prefs = _get_prefs()
    if prefs is None:
        return
    prefs.edit().putInt(constants.PREF_KEY_DEFAULT_COLOR, int(color)).apply()


def get_default_color():
    """获取默认颜色"""
    prefs = _get_prefs()
    if prefs is None:
        return constants.COLOR_TRANSPARENT_GRAY
    return prefs.getInt(constants.PREF_KEY_DEFAULT_COLOR, constants.COLOR_TRANSPARENT_GRAY)


def save_default_alpha(alpha):
    """保存默认透明度"""
    prefs = _get_prefs()
    if prefs is None:
        return
    prefs.edit().putFloat(constants.PREF_KEY_DEFAULT_ALPHA, float(alpha)).apply()


def get_default_alpha():
    """获取默认透明度"""
    prefs = _get_prefs()
    if prefs is None:
        return 1.0
    return prefs.getFloat(constants.PREF_KEY_DEFAULT_ALPHA, 1.0)


def save_service_enabled(enabled):
    """保存服务启用状态"""
    prefs = _get_prefs()
    if prefs is None:
        return
    prefs.edit().putBoolean(constants.PREF_KEY_ENABLED, enabled).apply()


def is_service_enabled():
    """获取服务启用状态"""
    prefs = _get_prefs()
    if prefs is None:
        return False
    return prefs.getBoolean(constants.PREF_KEY_ENABLED, False)


def clear_all():
    """清除所有保存的状态"""
    prefs = _get_prefs()
    if prefs is None:
        return
    prefs.edit().clear().apply()
