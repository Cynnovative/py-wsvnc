"""Key constants for user to press special keys."""

from typing import List

supported_versions: List[bytes] = [b"RFB 003.008\n"]

KEY_BackSpace = 0xFF08
KEY_Tab = 0xFF09
KEY_Return = 0xFF0D
KEY_Escape = 0xFF1B
KEY_Insert = 0xFF63
KEY_Delete = 0xFFFF
KEY_Home = 0xFF50
KEY_End = 0xFF57
KEY_PageUp = 0xFF55
KEY_PageDown = 0xFF56
KEY_Left = 0xFF51
KEY_Up = 0xFF52
KEY_Right = 0xFF53
KEY_Down = 0xFF54
KEY_F1 = 0xFFBE
KEY_F2 = 0xFFBF
KEY_F3 = 0xFFC0
KEY_F4 = 0xFFC1
KEY_F5 = 0xFFC2
KEY_F6 = 0xFFC3
KEY_F7 = 0xFFC4
KEY_F8 = 0xFFC5
KEY_F9 = 0xFFC6
KEY_F10 = 0xFFC7
KEY_F11 = 0xFFC8
KEY_F12 = 0xFFC9
KEY_F13 = 0xFFCA
KEY_F14 = 0xFFCB
KEY_F15 = 0xFFCC
KEY_F16 = 0xFFCD
KEY_F17 = 0xFFCE
KEY_F18 = 0xFFCF
KEY_F19 = 0xFFD0
KEY_F20 = 0xFFD1
KEY_ShiftLeft = 0xFFE1
KEY_ShiftRight = 0xFFE2
KEY_ControlLeft = 0xFFE3
KEY_ControlRight = 0xFFE4
KEY_MetaLeft = 0xFFE7
KEY_MetaRight = 0xFFE8
KEY_AltLeft = 0xFFE9
KEY_AltRight = 0xFFEA

KEY_Scroll_Lock = 0xFF14
KEY_Sys_Req = 0xFF15
KEY_Num_Lock = 0xFF7F
KEY_Caps_Lock = 0xFFE5
KEY_Pause = 0xFF13
KEY_Super_L = 0xFFEB  # windows-key, apple command key
KEY_Super_R = 0xFFEC  # windows-key, apple command key
KEY_Hyper_L = 0xFFED
KEY_Hyper_R = 0xFFEE

KEY_KP_0 = 0xFFB0
KEY_KP_1 = 0xFFB1
KEY_KP_2 = 0xFFB2
KEY_KP_3 = 0xFFB3
KEY_KP_4 = 0xFFB4
KEY_KP_5 = 0xFFB5
KEY_KP_6 = 0xFFB6
KEY_KP_7 = 0xFFB7
KEY_KP_8 = 0xFFB8
KEY_KP_9 = 0xFFB9
KEY_KP_Enter = 0xFF8D

KEY_ForwardSlash = 0x002F
KEY_BackSlash = 0x005C
KEY_SpaceBar = 0x0020
