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

def send(phone: int, message: str) -> None:
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
