"""Connection notice only; importing/showing it never accesses a camera."""

TITLE = 'Before connecting the camera, read this notice'
TEXT = (
    'When this tool connects to the camera or switches drivers, the camera showing '
    '"Please check the connected device" is normal.\n\n'
    'The computer may also stop showing the camera drive. Do not treat that camera message alone as a failed connection; '
    'check this tool\'s progress and full log. Success is decided by the tool\'s actual result.\n\n'
    'On macOS, camera operations open a Terminal window and use sudo to take over USB; enter your Mac login password '
    'in Terminal. The program never reads or stores the password. '
    'Closing the window before entering the password does not start any camera operation; once an operation starts, '
    'wait for it to finish and do not power off or unplug.\n\n'
    'Use Mass Storage mode and keep USB and power stable. '
    'While a task is running, do not unplug, power off or reinstall drivers because of this message. '
    'Only reconnect when the software explicitly asks you to, and only after all reads and writes have finished.\n\n'
    'If the tool itself reports an error, keep and export the diagnostic package; this normal connection message '
    'does not mean other errors can be ignored.'
)
