"""Matelotri Service — Limpieza auto + registro cliente + skin."""
import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui
import os
import json
import uuid
import platform

try:
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
except ImportError:
    from urllib2 import urlopen, Request
    from urllib import urlencode

ADDON = xbmcaddon.Addon()
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ICON = os.path.join(ADDON_PATH, 'icon.png')

HOME = xbmcvfs.translatePath('special://home/')
TEMP = xbmcvfs.translatePath('special://temp/')
PACKAGES = os.path.join(HOME, 'addons', 'packages')
ADDONS = os.path.join(HOME, 'addons')
USERDATA = xbmcvfs.translatePath('special://userdata/')

SKIN_ID = "skin.arctic.zephyr.mod"
SERVER_URL = "https://mortality-brown-largest-magnet.trycloudflare.com"
CLIENT_FILE = os.path.join(USERDATA, 'addon_data', 'plugin.program.matelotriwizard', 'client.json')


def log(msg):
    xbmc.log('[Matelotri Service] {}'.format(msg), xbmc.LOGINFO)


def get_device_name():
    try:
        info = json.loads(xbmc.executeJSONRPC(
            '{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params":{"labels":["System.FriendlyName"]},"id":1}'
        ))
        name = info.get('result', {}).get('System.FriendlyName', '')
        if name: return name
    except: pass
    return platform.node() or 'Kodi'


def register_client():
    """Registra cliente en el dashboard si no esta registrado."""
    try:
        # Check if already registered
        if os.path.exists(CLIENT_FILE):
            with open(CLIENT_FILE, 'r') as f:
                data = json.load(f)
                if data.get('id'):
                    log("Cliente ya registrado: {}".format(data['id']))
                    return data['id']

        # Register
        device = get_device_name()
        body = json.dumps({
            'nombre': device,
            'dispositivo': platform.system() + ' ' + platform.machine(),
            'telefono': '-'
        }).encode('utf-8')
        
        req = Request(SERVER_URL + '/api/register', data=body,
                      headers={'Content-Type': 'application/json'})
        resp = urlopen(req, timeout=10)
        result = json.loads(resp.read().decode('utf-8'))
        
        if result.get('ok') and result.get('id'):
            # Save client ID
            os.makedirs(os.path.dirname(CLIENT_FILE), exist_ok=True)
            with open(CLIENT_FILE, 'w') as f:
                json.dump({'id': result['id'], 'device': device}, f)
            log("Cliente registrado: {} ({})".format(result['id'], device))
            return result['id']
    except Exception as e:
        log("Error registro: {}".format(e))
    return None


def heartbeat(client_id):
    """Envia heartbeat al servidor."""
    try:
        body = json.dumps({'id': client_id}).encode('utf-8')
        req = Request(SERVER_URL + '/api/heartbeat', data=body,
                      headers={'Content-Type': 'application/json'})
        resp = urlopen(req, timeout=10)
        result = json.loads(resp.read().decode('utf-8'))
        return result.get('activo', True)
    except Exception as e:
        log("Error heartbeat: {}".format(e))
        return True


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
    addon_dir = ADDONS
    if not os.path.exists(addon_dir):
        return

    enabled = 0
    for addon_name in os.listdir(addon_dir):
        addon_xml = os.path.join(addon_dir, addon_name, 'addon.xml')
        if os.path.exists(addon_xml):
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
    skin_path = os.path.join(ADDONS, SKIN_ID)
    current_skin = xbmc.getSkinDir()

    if os.path.exists(skin_path) and current_skin != SKIN_ID:
        log("Skin {} instalado pero no activo (actual: {})".format(SKIN_ID, current_skin))
        xbmc.executeJSONRPC(
            '{{"jsonrpc":"2.0","method":"Settings.SetSettingValue",'
            '"params":{{"setting":"lookandfeel.skin","value":"{}"}},id":1}}'.format(SKIN_ID)
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

        # Registrar cliente en dashboard
        xbmc.sleep(3000)
        client_id = register_client()

    # Loop con heartbeat cada 5 min
    while not monitor.abortRequested():
        if monitor.waitForAbort(300):
            break
        if client_id:
            heartbeat(client_id)

