#!/bin/bash
# PORTMASTER: jellyfinrg35xx.zip, Jellyfin RG35XX.sh
XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}
if [ -d "/opt/system/Tools/PortMaster/" ]; then controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then controlfolder="$XDG_DATA_HOME/PortMaster"
else controlfolder="/roms/ports/PortMaster"; fi
source "$controlfolder/control.txt"
get_controls
GAMEDIR="/$directory/ports/jellyfinrg35xx"
CONFDIR="$GAMEDIR/conf"
mkdir -p "$CONFDIR"
# A second launch otherwise invalidates the first login and competes for video.
exec 9>"$GAMEDIR/.launcher.lock"
flock -n 9 || exit 0
cd "$GAMEDIR" || exit 1
> "$GAMEDIR/log.txt" && exec > >(tee "$GAMEDIR/log.txt") 2>&1
export XDG_CONFIG_HOME="$CONFDIR"
export XDG_DATA_HOME="$CONFDIR"
export SDL_GAMECONTROLLERCONFIG="$sdl_controllerconfig"
$GPTOKEYB "jellyfin_rg35xx.py" &
pm_platform_helper "$GAMEDIR/jellyfin_rg35xx.py"
python3 ./jellyfin_rg35xx.py
pm_finish
