# Sdílený ActivityWatch na jednom počítači (Linux)

Jeden Python server běží po startu počítače pod systémovým účtem `activitywatch`.
Každé grafické přihlášení spouští `aw-awatcher` pod přihlášeným uživatelem.
Watchery posílají na `127.0.0.1:5600` do bucketů
`aw-watcher-window_UZIVATEL_HOST` a `aw-watcher-afk_UZIVATEL_HOST`.
V Activity lze uživatele vybrat nabídkou **User**. Původní buckety bez jména jsou
pod **Legacy data (no user)**; původní data nelze dodatečně spolehlivě přiřadit.

## Instalace na Linuxu

1. Ukončete ActivityWatch přes ikonu v liště (**Quit**).
2. V aplikacích spouštěných po přihlášení vypněte původní spouštění `aw-qt` /
   ActivityWatch pro všechny účty, které ho mají zapnuté. Nové společné spouštění
   zajišťuje `/etc/xdg/autostart/activitywatch-session.desktop`.
3. Spusťte následující příkaz. Přenese kopii dosavadní uživatelské databáze
   a nainstaluje již přítomné GNOME rozšíření pro všechny účty:

```bash
cd /cesta/k/activitywatch
sudo bash scripts/multiuser/install.sh \
  "$HOME/.local/share/activitywatch/aw-server/peewee-sqlite.v2.db" \
  "$HOME/.local/share/gnome-shell/extensions/focused-window-dbus@flexagoon.com"
```

Původní databáze zůstává zachována. Pokud společná databáze už existuje,
instalátor ji odmítne přepsat. Pro aktualizaci existující instalace nejdříve
zastavte službu a spusťte instalátor bez argumentů:

```bash
sudo systemctl stop activitywatch-server.service
sudo bash scripts/multiuser/install.sh
```

4. Odhlaste a znovu přihlaste všechny grafické uživatele. Nově instalované
   GNOME rozšíření se zpřístupní po novém přihlášení a watcher ho zapne.
5. Otevřete <http://localhost:5600/> → **Activity** → **User**.
   Uživatelské jméno se objeví po prvním vytvoření jeho bucketů.
   `aw-qt` už nespouštějte: společný server běží nezávisle na přihlášení konkrétního uživatele.

Na každém účtu se sleduje jeho otevřená grafická relace. Odhlášený uživatel
nevytváří záznamy. Přepnutí či zamčení relace závisí na údajích o nečinnosti,
které poskytuje dané pracovní prostředí; nejde o sledování procesů všech účtů.
GNOME na Waylandu vyžaduje zapnuté rozšíření Focused Window D-Bus v každé relaci.
Pokud je systémová politika zakazuje, je nutné ji vyřešit ve správě GNOME.

Server naslouchá jen na tomto počítači. Jeho API a společná data jsou dostupná
všem místním uživatelům; filtr **User** slouží k výběru statistik, není řízením
přístupových práv. Přístup oddělený podle účtů tato instalace neposkytuje.

## Kontrola a umístění dat

```bash
systemctl status activitywatch-server.service
journalctl -u activitywatch-server.service -n 50
pgrep -a -u "$USER" -f /opt/activitywatch/aw-awatcher
```

Sdílená databáze:
`/var/lib/activitywatch/data/activitywatch/aw-server/peewee-sqlite.v2.db`.
Serverový účet nemá přihlašovací shell. Watcher nikdy neběží jako root.
Programy jsou v `/opt/activitywatch`, nezávisle na přístupu do domovského adresáře autora instalace.
Při aktualizaci zkopírujte novou sestavenou verzi instalátorem výše a odhlaste /
přihlaste uživatele, aby se spustily aktualizované watchery.

## Vypnutí automatického sledování

```bash
sudo systemctl disable --now activitywatch-server.service
sudo rm /etc/xdg/autostart/activitywatch-session.desktop
```

Běžící uživatelské watchery skončí po odhlášení. Data zůstanou zachována.

## Chyba „Too many open files“

Aktualizovaný server zavírá SQLite spojení po každém požadavku a systémová
služba nastavuje `LimitNOFILE=65536`. Po aktualizaci souborů v `dist` nasaďte
opravu (bez argumentu databáze, aby zůstala stávající sdílená data):

```bash
cd /cesta/k/activitywatch
sudo systemctl stop activitywatch-server.service
sudo bash scripts/multiuser/install.sh
systemctl show activitywatch-server.service -p LimitNOFILE -p LimitNOFILESoft
```
