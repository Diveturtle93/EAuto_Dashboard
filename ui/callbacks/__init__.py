#-----------------------------------------------------------------------
# Titel		:	__init__.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	16.06.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------
from .bms_outputs import registerBmsOutputsCallback
from .can_config import registerCanBannerCallback, registerCanConfigCallback
from .cell_data import registerCellDataCallbacks
from .ecu_preset import registerEcuPresetCallback
from .export_csv import registerExportCsvCallback
from .firmware_upload import registerFirmwareUploadCallback
from .reset import registerResetCallback
from .snapshot import registerSnapshotCallback
from .theme import registerThemeCallback
#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_CALLBACKS									= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
CALLBACKS_MAJOR									= 1
CALLBACKS_MINOR									= 0
CALLBACKS_PATCH									= 0
CALLBACKS_DEV									= 0
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------
__all__ = [
	"registerCanBannerCallback",
	"registerCanConfigCallback",
	"registerCellDataCallbacks",
	"registerBmsOutputsCallback",
	"registerEcuPresetCallback",
	"registerExportCsvCallback",
	"registerFirmwareUploadCallback",
	"registerResetCallback",
	"registerSnapshotCallback",
	"registerThemeCallback",
]
#-----------------------------------------------------------------------
