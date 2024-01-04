"""
This is solution from Torbjørn Kristoffersen.
https://medium.com/hackernoon/a-crude-imessage-api-efed29598e61
"""

import subprocess
import sys
import platform

mac_release, _, _ = platform.mac_ver()
if not mac_release:
    sys.exit(1)

def send(phone: int|str, message: str) -> None:
    """The phone can be eiter phone number or chat name."""
    try:
        int(phone)
    except ValueError:
        cmd = f"""\
    cat<<EOF | osascript - "{phone}" "{message}"
    on run {{targetGroup, targetMessage}}
    tell application "Messages"
        send targetMessage to chat targetGroup
    end tell
end run
EOF"""
    else:
        cmd = f"""\
    cat<<EOF | osascript - "{phone}" "{message}"
    on run {{targetBuddyPhone, targetMessage}}
    tell application "Messages"
        set targetService to 1st service whose service type = iMessage
        set targetBuddy to buddy targetBuddyPhone of targetService
        send targetMessage to targetBuddy
    end tell
end run
EOF"""
    subprocess.call(cmd, shell=True) 
