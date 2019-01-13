import json
import os
import subprocess
import shutil
import hashlib
import xml.etree.ElementTree as ET

def forceMkDir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

    os.mkdir(path)

def parseAddonList(path):
    with open("addons.json", encoding="utf-8") as file:
        data = json.loads(file.read())

    return data

def copyAddonResources(id, xmlElement):
    if xmlElement is not None:
        dir = os.path.dirname(xmlElement.text)
        path = os.path.join(id, dir)

        if not os.path.isdir(path):
            os.mkdir(path)

        shutil.copy(os.path.join("tmp", xmlElement.text), os.path.join(id, xmlElement.text))


def updateAddons(addons):
    for addon in addons:
        id = addon["id"]

        forceMkDir("tmp")

        subprocess.call(["git", "clone", addon["git"], "tmp"])
        subprocess.call(["make", "package"], cwd="tmp")
        
        forceMkDir(id)
        
        shutil.copy("tmp/addon.xml", id)

        a = ET.parse("tmp/addon.xml").getroot()
        r = a.find('extension[@point="xbmc.addon.metadata"]/assets')
        if r is not None:
            icon = r.find("icon")
            fanart = r.find("fanart")

            copyAddonResources(id, icon)
            copyAddonResources(id, fanart)

        packages = os.listdir("tmp/dist")
        for package in packages:
            shutil.copy(os.path.join("tmp", "dist", package), id)

def updateAddonsManifest(addons):
    addonXMLRoots = []

    def addAddonXMLRoot(id):
        root = ET.parse(os.path.join(id, "addon.xml")).getroot()
        addonXMLRoots.append(root)

    addAddonXMLRoot("repository.chrisxf")
    
    for addon in addons:
        addAddonXMLRoot(addon["id"])

    addonsRoot = ET.Element("addons")
    for root in addonXMLRoots:
        addonsRoot.append(root)

    tree = ET.ElementTree(addonsRoot)
    tree.write("addons.xml")

def updateAddonsHash(addons):
    addonData = []

    def scanAddonData(id):
        d = subprocess.check_output(["find", id, "-type", "f", "-printf", "%p %TY-%Tm-%Td %TH:%TM:%TS %Tz %s"])
        addonData.append(d.decode("UTF-8"))

    scanAddonData("repository.chrisxf")

    for addon in addons:
        scanAddonData(addon["id"])

    m = hashlib.md5("".join(addonData).encode("utf-8"))
    f = os.open("addons.xml.md5", os.O_RDWR|os.O_CREAT)
    os.write(f, m.hexdigest().encode("utf-8"))

addons = parseAddonList("addons.json")
updateAddons(addons)
updateAddonsManifest(addons)
updateAddonsHash(addons)

if os.path.isdir("tmp"):
    shutil.rmtree("tmp")