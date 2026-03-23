import re
from typing import List

import mobase

# import html2text
from .html2text import html2text

try:
    from PyQt6.QtWidgets import QMessageBox
except ImportError:
    from PyQt5.QtWidgets import QMessageBox


class MO2ModlistReportGenerator(mobase.IPluginTool):
    _organizer: mobase.IOrganizer
    _modList: mobase.IModList
    _pluginList: mobase.IPluginList
    _archiveList: list[str]

    _isMo2Updated: bool

    def __init__(self):
        super().__init__()

    def init(self, organizer: mobase.IOrganizer):
        self._organizer = organizer
        self._modList = organizer.modList()
        self._pluginList = organizer.pluginList()
        self._archiveList = []

        version = self._organizer.appVersion().canonicalString()
        versionx = re.sub("[^0-9.]", "", version)
        self._version = float(".".join(versionx.split(".", 2)[:-1]))
        self._isMo2Updated = self._version >= 2.5
        return True

    # Basic info
    def name(self) -> str:
        return "Report Generator"

    def author(self) -> str:
        return "Lazyelm & rux616"

    def description(self) -> str:
        return "Generates a modlist report with useful info like links to source and plugins with priority"

    def version(self) -> mobase.VersionInfo:
        return mobase.VersionInfo(0, 0, 2, mobase.ReleaseType.PRE_ALPHA)

    # Settings
    def isActive(self) -> str:
        return self._organizer.managedGame().feature(mobase.GamePlugins)

    def settings(self) -> List[mobase.PluginSetting]:
        return [
            mobase.PluginSetting("enabled", "enable this plugin", True)
            # Add Settings Later for file location etc...(this isn't working as expected yet for me)
            # mobase.PluginSetting("enabled", "enable this plugin", True),
            # mobase.PluginSetting("saveDestination", "Where to save file", "./profiles"),
            # mobase.PluginSetting("saveFileName", "What shall we call the file?", "MO2ModlistReport.csv"),
        ]

    # Display
    def displayName(self) -> str:
        return "Report Generator"

    def tooltip(self) -> str:
        return "Exports modlist to a CSV with useful info like links to source and plugins with priority"

    def icon(self):
        if self._isMo2Updated:
            from PyQt6.QtGui import QIcon
        else:
            from PyQt5.QtGui import QIcon

        return QIcon()

    def cleanStr(self, s):
        s = str(s)
        if s.__len__() >= 1:
            s = html2text(s)
            s = self.quote(s)
            return s
        else:
            return s

    def quote(self, s):
        s = str(s)
        if s.__len__() > 0:
            return '"' + s + '"'
        else:
            return s

    def populateArchives(self, path: str, fileTreeEntry: mobase.FileTreeEntry) -> mobase.IFileTree.WalkReturn:
        if fileTreeEntry.isDir():
            return mobase.IFileTree.WalkReturn.SKIP
        elif fileTreeEntry.suffix().lower() in ["ba2", "bsa"]:
            self._archiveList.append(fileTreeEntry.path())
        return mobase.IFileTree.WalkReturn.CONTINUE

    def debugMsg(self, s):
        msgBox = QMessageBox()
        msgBox.setText(s)
        msgBox.exec()
        return

    # Plugin Logic
    def display(self) -> bool:
        # Define File Location
        outputName = "MO2ModlistReport.csv"
        outputPath = self._organizer.profilePath()
        outputLocation = outputPath + "/" + outputName

        # Get All Mods by Priority
        allMods = self._modList.allModsByProfilePriority()

        # Get All Plugins
        allPlugins = self._pluginList.pluginNames()

        # Clear File if Exists
        with open(outputLocation, "w") as f:
            f.write(
                ", ".join(
                    [
                        "Mod Name",
                        "Enabled",
                        "Mod URL",
                        # "Comment",
                        "Categories",
                        # "Notes",
                        "Plugins",
                        "Archives",
                    ]
                )
                + "\n"
            )

        # Loop through all mods and get each ones detail and append to CSV file
        for mod in allMods:
            # Get Mod Info
            outputString = ""
            modObj = self._modList.getMod(mod)
            self._archiveList = []
            modObj.fileTree().walk(self.populateArchives)

            modName = modObj.name()
            modNameQuoted = self.quote(modName)
            modEnabled = str(bool(self._modList.state(modName) & mobase.ModState.ACTIVE))
            modUrl = modObj.url()
            modGame = modObj.gameName().lower()
            modNexusId = str(modObj.nexusId())
            modComment = self.quote(modObj.comments())
            modCats = self.quote("\n".join(modObj.categories()))
            modNotes = self.cleanStr(modObj.notes())

            # Get Plugin Info for Mod
            pluginString = self.quote(
                ",".join(
                    [
                        f"<{self._pluginList.priority(plugin)}>{plugin}"
                        for plugin in allPlugins
                        if self._pluginList.origin(plugin) == modName
                    ]
                )
            )

            # Get Archive Info for Mod
            archiveString = self.quote(", ".join([f"{archive}" for archive in sorted(self._archiveList)]))

            # Build Text Line
            if modObj.isSeparator():
                modName = modName[0 : modName.rfind("_separator")]  # remove trailing "_separator"
                modNameQuoted = self.quote(f"{modName} (Separator)")
                modEnabled = ""

            if modObj.isForeign():
                modEnabled = ""
                archiveString = ""

            urlString = ""
            if modObj.nexusId() <= 0 or modUrl != "":
                urlString = modUrl
            else:
                urlString = f"https://www.nexusmods.com/{modGame}/mods/{modNexusId}"

            outputString = ",".join(
                [
                    modNameQuoted,
                    modEnabled,
                    urlString,
                    # modComment,
                    modCats,
                    # modNotes,
                    pluginString,
                    archiveString,
                ]
            )

            with open(outputLocation, "a", encoding="utf-8-sig") as f:
                f.write(outputString + "\n")

            # clear archive list for next mod
            self._archiveList.clear()

        msgBox = QMessageBox()
        msgBox.setText("Modlist report has been generated!\nYou can find the report at:\n\n" + outputLocation)
        msgBox.exec()


# Tell Mod Organizer to initialize the plugin
def createPlugin() -> mobase.IPlugin:
    return MO2ModlistReportGenerator()
