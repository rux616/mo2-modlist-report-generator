import mobase
import re
from typing import List

# import html2text
from .html2text import html2text


try:
    from PyQt6.QtWidgets import QMessageBox
except ImportError:
    from PyQt5.QtWidgets import QMessageBox


class LazyListExport(mobase.IPluginTool):
    _organizer: mobase.IOrganizer
    _modList: mobase.IModList
    _pluginList: mobase.IPluginList

    _isMo2Updated: bool

    def __init__(self):
        super().__init__()

    def init(self, organizer: mobase.IOrganizer):
        self._organizer = organizer
        self._modList = organizer.modList()
        self._pluginList = organizer.pluginList()

        version = self._organizer.appVersion().canonicalString()
        versionx = re.sub("[^0-9.]", "", version)
        self._version = float(".".join(versionx.split(".", 2)[:-1]))
        self._isMo2Updated = self._version >= 2.5
        return True

    # Basic info
    def name(self) -> str:
        return "Lazy Modlist Export"

    def author(self) -> str:
        return "Lazyelm"

    def description(self) -> str:
        return "Exports Modlist as CSV with Name and URL"

    def version(self) -> mobase.VersionInfo:
        return mobase.VersionInfo(0, 0, 2, mobase.ReleaseType.PRE_ALPHA)

    # Settings
    def isActive(self) -> str:
        return self._organizer.managedGame().feature(mobase.GamePlugins)

    def settings(self) -> List[mobase.PluginSetting]:
        return [
            mobase.PluginSetting("enabled", "enable this plugin", True)
            # Add Settings Later for file location etc...(this isnt working as expected yet for me)
            # mobase.PluginSetting("enabled", "enable this plugin", True),
            # mobase.PluginSetting("saveDestination", "Where to save file", "./profiles"),
            # mobase.PluginSetting("saveFileName", "What shall we call the file?", "LazyModlistExporter.csv"),
        ]

    # Display
    def displayName(self) -> str:
        return "Lazy Modlist Export"

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

    def debugMsg(self, s):
        msgBox = QMessageBox()
        msgBox.setText(s)
        msgBox.exec()
        return

    # Plugin Logic
    def display(self) -> bool:
        # Define File Location
        outputName = "LazyListExporter.csv"
        outputPath = self._organizer.profilePath()
        outputLocation = outputPath + "/" + outputName

        # Get All Mods by Priority
        allMods = self._modList.allModsByProfilePriority()

        # Get All Plugins
        allPlugins = self._pluginList.pluginNames()

        # Clear File if Exists
        with open(outputLocation, "w") as f:
            f.write(
                "Mod Name, Mod URL, Nexus URL, Comment, Categories, Notes, Plugins --> \n"
            )

        # Loop through all mods and get each ones detail and append to CSV file
        for mod in allMods:
            # Get Mod Info
            outputString = ""
            modObj = self._modList.getMod(mod)

            modName = modObj.name()
            modUrl = modObj.url()
            modNexusId = str(modObj.nexusId())
            modComment = self.quote(modObj.comments())
            modCats = self.quote("\n".join(modObj.categories()))
            modNotes = self.cleanStr(modObj.notes())

            # Get Plugin Info for Mod
            pluginString = ""
            for plugin in allPlugins:
                if self._pluginList.origin(plugin) == modName:
                    pluginString = (
                        pluginString
                        + str(self._pluginList.priority(plugin))
                        + " - "
                        + plugin
                        + ","
                    )

            # Build Text Line
            if modObj.isSeparator():
                outputString = "\n-------------------" + modName + "-------------------"
            else:
                urlString = ""
                if modObj.nexusId() <= 0:
                    urlString = ""
                else:
                    urlString = (
                        "https://www.nexusmods.com/skyrimspecialedition/mods/"
                        + modNexusId
                    )
                outputString = (
                    modName
                    + ","
                    + modUrl
                    + ","
                    + urlString
                    + ","
                    + modComment
                    + ","
                    + modCats
                    + ","
                    + modNotes
                    + ","
                    + pluginString
                )

            with open(outputLocation, "a", encoding="utf-8-sig") as f:
                f.write(outputString + "\n")

        msgBox = QMessageBox()
        msgBox.setText(
            "Lazy Modlist Exporter is complete!\nYou can find your modlist export at:\n\n"
            + outputLocation
        )
        msgBox.exec()


# Tell Mod Organizer to initialize the plugin
def createPlugin() -> mobase.IPlugin:
    return LazyListExport()
