"""Matelotri Service — Limpieza auto + activar skin al inicio."""
import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui
import os
import json

ADDON = xbmcaddon.Addon()
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ICON = os.path.join(ADDON_PATH, 'icon.png')

HOME = xbmcvfs.translatePath('special://home/')
TEMP = xbmcvfs.translatePath('special://temp/')
PACKAGES = os.path.join(HOME, 'addons', 'packages')
ADDONS = os.path.join(HOME, 'addons')

SKIN_ID = "skin.arctic.zephyr.mod"


def log(msg):
    xbmc.log('[Matelotri Service] {}'.format(msg), xbmc.LOGINFO)


def clean_on_boot():
    cleaned = 0
    for d in [PACKAGES, os.path.join(HOME, 'cache'), TEMP]:
        if os.path.exists(d):
            for f in os.listdir(d):
                try:
                    fp = os.path.join(d, f)
                    if os.path.isfile(fp):
                        os.remove(fp)
                        cleaned += 1
                except:
                    pass
    return cleaned


def enable_addons():
    """Habilita addons instalados que no esten en la DB."""
    addon_dir = ADDONS
    if not os.path.exists(addon_dir):
        return

    enabled = 0
    for addon_name in os.listdir(addon_dir):
        addon_xml = os.path.join(addon_dir, addon_name, 'addon.xml')
        if os.path.exists(addon_xml):
            # Intentar habilitar via JSONRPC
            result = xbmc.executeJSONRPC(
                '{{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled",'
                '"params":{{"addonid":"{}","enabled":true}},"id":1}}'.format(addon_name)
            )
            try:
                r = json.loads(result)
                if 'result' in r and r['result'] == 'OK':
                    enabled += 1
            except:
                pass

    if enabled > 0:
        log("Habilitados {} addons".format(enabled))
    return enabled


def check_skin():
    """Si el skin Arctic Zephyr esta instalado pero no activo, ofrece activarlo."""
    skin_path = os.path.join(ADDONS, SKIN_ID)
    current_skin = xbmc.getSkinDir()

    if os.path.exists(skin_path) and current_skin != SKIN_ID:
        log("Skin {} instalado pero no activo (actual: {})".format(SKIN_ID, current_skin))
        # Activar automaticamente
        xbmc.executeJSONRPC(
            '{{"jsonrpc":"2.0","method":"Settings.SetSettingValue",'
            '"params":{{"setting":"lookandfeel.skin","value":"{}"}},"id":1}}'.format(SKIN_ID)
        )
        log("Skin {} activado".format(SKIN_ID))


if __name__ == '__main__':
    monitor = xbmc.Monitor()

    # Esperar a que Kodi este listo
    xbmc.sleep(8000)

    if not monitor.abortRequested():
        # Limpieza
        log("Limpieza automatica...")
        n = clean_on_boot()
        if n > 0:
            xbmcgui.Dialog().notification(
                "[COLOR gold]Matelotri[/COLOR]",
                "{} archivos limpiados".format(n), ICON, 3000)

        # Habilitar addons
        xbmc.sleep(2000)
        enable_addons()

        # Verificar skin
        xbmc.sleep(2000)
        check_skin()

    while not monitor.abortRequested():
        if monitor.waitForAbort(300):
            break
