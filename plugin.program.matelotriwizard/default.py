"""Matelotri Wizard v3.0 — Build con Matelotri Cinema + IPTV."""
import sys
import os
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import xbmc

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ICON = os.path.join(ADDON_PATH, 'icon.png')
FANART = os.path.join(ADDON_PATH, 'fanart.png')
MEDIA = os.path.join(ADDON_PATH, 'resources', 'media')

HOME = xbmcvfs.translatePath('special://home/')
USERDATA = xbmcvfs.translatePath('special://userdata/')
PACKAGES = os.path.join(HOME, 'addons', 'packages')
TEMP = xbmcvfs.translatePath('special://temp/')

BUILD_NAME = "Matelotri Cinema"
BUILD_URL = "https://github.com/actualizarcabel2-prog/matelotri-repo/releases/download/v1.0.0/matelotri_build.zip"


def add_item(handle, label, action, icon_name, desc=""):
    li = xbmcgui.ListItem(label)
    icon_path = os.path.join(MEDIA, icon_name) if os.path.exists(os.path.join(MEDIA, icon_name)) else ICON
    li.setArt({'icon': icon_path, 'thumb': icon_path, 'fanart': FANART})
    if desc:
        li.setInfo('video', {'plot': desc})
    url = "plugin://{}/?action={}".format(ADDON_ID, action)
    xbmcplugin.addDirectoryItem(handle, url, li, False)


def add_sep(handle, text):
    li = xbmcgui.ListItem("[COLOR gold]━━━ {} ━━━[/COLOR]".format(text))
    li.setArt({'icon': ICON, 'fanart': FANART})
    xbmcplugin.addDirectoryItem(handle, "", li, False)


def menu(handle):
    add_sep(handle, "🎬  M A T E L O T R I  🎬")
    add_item(handle, "[COLOR gold][B]📥 Instalar Build Completa[/B][/COLOR]", "install_build", "builds.png",
        "Instala Matelotri Cinema con:\n• Addon Peliculas/Series/Anime (AllDebrid)\n• PVR IPTV Simple Client (TDT España)\n• Configuracion completa\n\nKodi se cerrara al terminar.")
    add_sep(handle, "🔧  MANTENIMIENTO")
    add_item(handle, "[COLOR deepskyblue]🧹 Limpieza Profunda[/COLOR]", "deep_clean", "clean.png",
        "Cache + paquetes + temporales.")
    add_item(handle, "[COLOR deepskyblue]🗑️ Solo Cache[/COLOR]", "clean_cache", "maintenance.png", "")
    add_item(handle, "[COLOR deepskyblue]📦 Solo Paquetes[/COLOR]", "clean_packages", "settings.png", "")
    add_sep(handle, "⚡  SISTEMA")
    add_item(handle, "[COLOR tomato]🔄 Reiniciar Limpio[/COLOR]", "restart_clean", "power.png", "Limpia + cierra.")
    add_item(handle, "[COLOR tomato]⚡ Forzar Cierre[/COLOR]", "force_close", "power.png", "")
    add_item(handle, "[COLOR white]📋 Info[/COLOR]", "about", "info.png", "v3.0")
    xbmcplugin.endOfDirectory(handle)


def _download(url, dest, progress, label):
    from urllib.request import urlopen, Request
    req = Request(url, headers={'User-Agent': 'Kodi/21'})
    resp = urlopen(req, timeout=300)
    total = int(resp.headers.get('Content-Length', 0))
    got = 0
    with open(dest, 'wb') as f:
        while True:
            if progress.iscanceled():
                return False
            buf = resp.read(65536)
            if not buf:
                break
            f.write(buf)
            got += len(buf)
            if total > 0:
                pct = int(got * 100 / total)
                progress.update(pct, "{} - {:.1f}/{:.1f} MB".format(label, got/1048576, total/1048576))
    return True


def _extract(zip_path, progress, label):
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = [n for n in zf.namelist() if not n.endswith('/')]
        total = len(names)
        for i, name in enumerate(names):
            if name.startswith('addons/'):
                dest = os.path.join(HOME, name)
            elif name.startswith('userdata/'):
                rel = name[len('userdata/'):]
                dest = os.path.join(USERDATA, rel)
            elif name.startswith('addon_data/'):
                dest = os.path.join(USERDATA, name)
            else:
                dest = os.path.join(USERDATA, name)
            dest_dir = os.path.dirname(dest)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            if not name.endswith('/'):
                try:
                    data = zf.read(name)
                    with open(dest, 'wb') as out:
                        out.write(data)
                except:
                    pass
            if i % 10 == 0:
                progress.update(int(i*100/max(total,1)), "{} - {}/{}".format(label, i, total))
    return True


def install_build():
    dialog = xbmcgui.Dialog()
    if not dialog.yesno("[COLOR gold]Matelotri Cinema[/COLOR]",
        "[B]Instalar Build Completa?[/B]\n\n"
        "Se descargara e instalara:\n"
        "• Matelotri Cinema (Pelis, Series, Anime)\n"
        "• PVR IPTV Simple Client (TDT)\n"
        "• Configuracion AllDebrid + servidor\n\n"
        "[COLOR tomato]Kodi se cerrara al terminar.[/COLOR]"):
        return

    # Pedir datos del cliente
    nombre = dialog.input("[COLOR gold]Matelotri[/COLOR] — Tu nombre de usuario", type=xbmcgui.INPUT_ALPHANUM)
    if not nombre:
        nombre = "Cliente"
    contrasena = dialog.input("[COLOR gold]Matelotri[/COLOR] — Contraseña", type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
    if not contrasena:
        contrasena = ""
    telefono = dialog.input("[COLOR gold]Matelotri[/COLOR] — Tu teléfono", type=xbmcgui.INPUT_ALPHANUM)
    if not telefono:
        telefono = "-"

    # Registrar en el servidor
    try:
        import json, platform
        try:
            from urllib.request import urlopen, Request
        except ImportError:
            from urllib2 import urlopen, Request

        SERVER_URL = "https://mortality-brown-largest-magnet.trycloudflare.com"
        body = json.dumps({
            'nombre': nombre,
            'contrasena': contrasena,
            'telefono': telefono,
            'dispositivo': platform.system() + ' ' + platform.machine()
        }).encode('utf-8')
        req = Request(SERVER_URL + '/api/register', data=body,
                      headers={'Content-Type': 'application/json'})
        resp = urlopen(req, timeout=10)
        result = json.loads(resp.read().decode('utf-8'))

        if result.get('ok') and result.get('id'):
            # Guardar ID del cliente
            client_dir = os.path.join(USERDATA, 'addon_data', 'plugin.program.matelotriwizard')
            if not os.path.exists(client_dir):
                os.makedirs(client_dir)
            with open(os.path.join(client_dir, 'client.json'), 'w') as f:
                json.dump({'id': result['id'], 'nombre': nombre, 'telefono': telefono}, f)
            xbmc.log('[Matelotri] Cliente registrado: {} ({})'.format(nombre, result['id']), xbmc.LOGINFO)
    except Exception as e:
        xbmc.log('[Matelotri] Error registro: {}'.format(e), xbmc.LOGINFO)

    if not os.path.exists(PACKAGES):
        os.makedirs(PACKAGES)

    zip_path = os.path.join(PACKAGES, 'matelotri_build.zip')
    progress = xbmcgui.DialogProgress()

    # Descargar
    progress.create("[COLOR gold]Matelotri[/COLOR]", "Descargando build...")
    try:
        ok = _download(BUILD_URL, zip_path, progress, "Matelotri Build")
        if not ok:
            progress.close()
            dialog.ok("Matelotri", "Descarga cancelada")
            return
    except Exception as e:
        progress.close()
        dialog.ok("Error", str(e))
        return
    progress.close()

    # Extraer
    progress.create("[COLOR gold]Matelotri[/COLOR]", "Extrayendo build...")
    try:
        _extract(zip_path, progress, "Instalando")
    except Exception as e:
        progress.close()
        dialog.ok("Error", str(e))
        return
    progress.close()

    # Limpiar
    try:
        os.remove(zip_path)
    except:
        pass

    dialog.ok("[COLOR gold]Matelotri Cinema[/COLOR]",
        "[B]Build instalada![/B]\n\n"
        "Bienvenido {}!\n"
        "Kodi se cerrara ahora.\n\n"
        "[COLOR gold]Al reabrir: cine en casa! 🎬[/COLOR]".format(nombre))
    xbmc.executebuiltin('Quit')


def deep_clean():
    if not xbmcgui.Dialog().yesno("[COLOR gold]Matelotri[/COLOR]", "Limpieza profunda?"):
        return
    n = _clean(os.path.join(HOME,'cache')) + _clean(PACKAGES) + _clean(TEMP)
    xbmcgui.Dialog().ok("[COLOR gold]Matelotri[/COLOR]", "[B]{} archivos eliminados[/B]".format(n))

def clean_cache():
    n = _clean(os.path.join(HOME,'cache')) + _clean(TEMP)
    xbmcgui.Dialog().notification("[COLOR gold]Matelotri[/COLOR]", "{} eliminados".format(n), ICON, 3000)

def clean_packages():
    n = _clean(PACKAGES)
    xbmcgui.Dialog().notification("[COLOR gold]Matelotri[/COLOR]", "{} paquetes eliminados".format(n), ICON, 3000)

def restart_clean():
    if not xbmcgui.Dialog().yesno("[COLOR gold]Matelotri[/COLOR]", "Limpiar y cerrar?"):
        return
    _clean(os.path.join(HOME,'cache')); _clean(PACKAGES); _clean(TEMP)
    xbmc.sleep(1000)
    xbmc.executebuiltin('Quit')

def force_close():
    if xbmcgui.Dialog().yesno("[COLOR gold]Matelotri[/COLOR]", "Cerrar Kodi?"):
        xbmc.executebuiltin('Quit')

def about():
    xbmcgui.Dialog().ok("[COLOR gold]Matelotri Cinema v3.0[/COLOR]",
        "Addon: Peliculas, Series, Anime, Docs\nIPTV: TDT España (PVR Simple Client)\nStreaming: AllDebrid via Worker\n\n🎬 Para cinefilos")

def _clean(path):
    n = 0
    if os.path.exists(path):
        for f in os.listdir(path):
            try:
                fp = os.path.join(path, f)
                if os.path.isfile(fp): os.remove(fp); n += 1
            except: pass
    return n


if __name__ == '__main__':
    handle = int(sys.argv[1])
    params = sys.argv[2].lstrip('?')
    if not params:
        menu(handle)
    else:
        a = dict(x.split('=') for x in params.split('&') if '=' in x).get('action','')
        {'install_build':install_build,'deep_clean':deep_clean,
         'clean_cache':clean_cache,'clean_packages':clean_packages,'restart_clean':restart_clean,
         'force_close':force_close,'about':about}.get(a, lambda:None)()
