import tkinter as tk  # GUI
from tkinter import scrolledtext as st  # Text widget
from tkinter import messagebox as mb  # Error box
import requests  # Get translator from github
import os  # Check if files exist, create directory and find helperlog
import datetime  # Print update time
import json  # To read dictionary
import shutil  # To delete directory, only for testing purposes

# For text widget
TEXT_HEIGHT = 10
TEXT_WIDTH = 22
# Helper log paths
PATH = os.getenv('LOCALAPPDATA') + \
    'Low/Team Cherry/Hollow Knight/Randomizer 4/Recent/HelperLog.txt'
NEWPATH = os.getenv(
    'LOCALAPPDATA') + 'Low/Team Cherry/Hollow Knight/Randomizer 4/Recent/HelperLogTrans.txt'
# Path for files used by program
INNERPATH = 'usedFiles'
JSONPATH = INNERPATH + '/mapDict.json'
GOODJSONPATH = INNERPATH + '/mapDictR.json'
CONFIGPATH = INNERPATH + '/config.ini'
XMLPATH = INNERPATH + '/mapDict.xml'
XMLURL = 'https://raw.githubusercontent.com/ManicJamie/HKTranslator/master/TranslatorDictionary.xml'
# All possible blocs in HelperLog.txt
# MAP RANDOMIZER MUST GO AT THE END
SETTINGS = ['UNCHECKED REACHABLE LOCATIONS',
            'PREVIEWED LOCATIONS',
            'UNCHECKED REACHABLE TRANSITIONS',
            'CHECKED TRANSITIONS',
            'RESPAWNING ITEMS',
            'REGION NAMES',
            'ADD REVERSED TRANSITIONS']
# To make stuff automatic, for future updates maybe
NB_TO_IGNORE = 2
MAP_OPTION_POS = -2


def errorBoxQuit(string):
    mb.showerror("Error", string)
    quit()


def toggleTrans():
    '''Function called by toggle_button to resume/pause translation'''
    global running
    running = not running

    if running:
        toggle_text.set('Pause translation')
        addText('\nTranslation resumed.')
    else:
        toggle_text.set('Resume translation')
        addText('\nTranslation paused.')


def openFile():
    '''Opens translated file with default app for .txt files'''
    if os.path.isfile(NEWPATH):
        os.startfile(NEWPATH)
        addText('\nOpening file.')
    else:
        addText('\nFile not found...')


def addText(string):
    '''Adds argument to text widget and makes it read only'''
    main_stext.config(state=tk.NORMAL)

    nbLines = int(main_stext.index('end').split('.')[0]) - 1
    if nbLines >= 10:
        # Delete first line to keep everything in view
        main_stext.delete('1.0', '2.0')
    main_stext.insert(tk.INSERT, string)

    main_stext.config(state=tk.DISABLED)


def updateSettings():
    '''Gets which blocs to place in translated file from checkboxes'''
    tab = []
    for i in range(len(varnames) - NB_TO_IGNORE):
        # Uses general names from setup
        if globals()[varnames[i]].get():
            tab.append(SETTINGS[i])

    return tab


def updateLoop():
    '''Main loop, repeats until window is closed'''
    global prevToWrite
    global toWrite

    if running:
        # Get what to write
        settingsTab = updateSettings()

        # Get helper log contents
        try:
            with open(PATH, 'r') as f:
                helperLog = f.read()
        except Exception as e:
            errorBoxQuit('HelperLog not found. ' + str(e))

        blocs = helperLog.split('\n\n')
        toWrite = ''

        for bloc in blocs:
            # Add only wanted blocs
            if bloc.split('\n')[0] in settingsTab:
                if bloc.split('\n')[0] in \
                        ['CHECKED TRANSITIONS', 'UNCHECKED REACHABLE TRANSITIONS']:
                    for word in translationDict:
                        # find position of word and next '['
                        if word in bloc:
                            wordPos = bloc.index(word)
                            bracketPos = bloc.index('[', wordPos)
                            if not globals()[varnames[MAP_OPTION_POS]].get():
                                ### This is a map rando
                                mapName = translationDict[word]['map']
                                shortName = translationDict[word]['short_name']
                                newName = f"{mapName}[{shortName}]"
                                bloc = bloc.replace(
                                    bloc[wordPos:bracketPos],
                                    newName)
                            else:
                                ### This is an area rando
                                areaName = translationDict[word]['area']
                                shortName = translationDict[word]['short_name']
                                newName = f"{areaName}[{shortName}]"
                                bloc = \
                                    bloc.replace(
                                        bloc[wordPos:bracketPos],
                                        newName)

                    splitbloc = bloc.split('\n')
                    blocName = splitbloc[0]
                    lines = splitbloc[1:]
                    if blocName == "UNCHECKED REACHABLE TRANSITIONS":
                        newbloc = blocName + '\n' + '\n'.join(sorted(lines))
                        toWrite += newbloc + '\n\n'
                    elif blocName == "CHECKED TRANSITIONS":
                        # Get all reversable transitions
                        transTab = list(map(
                            lambda x: x[2:].split('  -->  '),
                            lines))
                        reversableTab = []
                        if not globals()[varnames[-1]].get():
                            cyclebloc = 'REVERSABLE ' + blocName
                        else:
                            cyclebloc = 'REPEATED REVERSABLE ' + blocName
                        for trans in transTab:
                            origin = trans[0]
                            for trans2 in transTab:
                                if origin == trans2[1] and trans not in reversableTab \
                                        and trans[::-1] not in reversableTab:
                                    reversableTab.append(trans)
                                    if globals()[varnames[-1]].get():
                                        reversableTab.append(trans[::-1])

                        reversableTab = sorted(reversableTab)

                        for x in reversableTab:
                            if x in transTab:
                                transTab.remove(x)
                            if x[::-1] in transTab:
                                transTab.remove(x[::-1])
                            cyclebloc += '\n  ' + '  <->  '.join(x)

                        toWrite += cyclebloc + '\n\n'

                        onewaybloc = 'ONEWAY ' + blocName
                        for x in transTab:
                            onewaybloc += '\n  ' + '  -->  '.join(x)
                        toWrite += onewaybloc + '\n\n'
                else:
                    toWrite += bloc + '\n\n'

        if toWrite != prevToWrite:  # We need to update!
            # Get update time
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            addText(f'\nUpdated at {current_time}.')

            # Write file
            try:
                with open(NEWPATH, 'w') as f:
                    f.write(toWrite)
            except Exception as e:
                errorBoxQuit('Cannot write translated file. ' + str(e))

    prevToWrite = toWrite
    root.after(100, updateLoop)  # Recursion loop


def writeConfig():
    '''Writes config to file to save settings for the checkboxes'''
    string = ''
    for i in range(len(varnames)):
        string += str(globals()[varnames[i]].get())
    try:
        with open(CONFIGPATH, 'w') as f:
            f.write(string)
    except Exception as e:
        errorBoxQuit('Cannot write config file. ' + str(e))


def readConfig():
    if os.path.isfile(CONFIGPATH):
        with open(CONFIGPATH, 'r') as f:
            configFile = f.read()
        if len(configFile) == len(SETTINGS):
            configString = 'Config.ini found.\n'
        else:
            configString = 'Config size error.\nConfig.ini created.\n'
            configFile = '010' + '1' * (len(SETTINGS) - 3)
    else:
        configFile = '010' + '1' * (len(SETTINGS) - 3)
        configString = 'Config.ini created.\n'

    return configFile, configString


def createJSON():
    """This creates a good dictionary but region names may not be right"""
    if not os.path.isfile(JSONPATH):
        # Use XML to create JSON
        if not os.path.isfile(XMLPATH):
            # Need to download XML
            addText('Downloading XML.\n')
            try:
                r = requests.get(XMLURL, allow_redirects=True)
                open(XMLPATH, 'wb').write(r.content)
            except Exception as e:
                errorBoxQuit(
                    "Could not find or download TranslatorDictionary.xml. " + str(e))

        # Read XML and create dictionary from it
        with open(XMLPATH) as f:
            dictStr = f.read()

        # Isolate old names
        oldSplit = dictStr.split('<oldName>')
        oldNames = []
        for line in oldSplit:
            if '</oldName>' in line:
                oldNames.append(line.split('</oldName>')[0])
        oldSplit = dictStr.split('<newName>')
        # Isolate new names
        newNames = []
        for line in oldSplit:
            if '</newName>' in line:
                newNames.append(line.split('</newName>')[0])
        assert len(oldNames) == len(newNames)  # just in case

        # Create dictionary
        locDict = {}

        # Fill dictionary with extracted names
        # TODO this code could be way more clean, maybe in another function
        # Could be hardcoded but wouldn't fit with the goal of building the files
        for i in range(len(oldNames)):
            room_name = newNames[i]
            room_name_no_area = '_'.join(newNames[i].split('_')[1:])
            map_name = newNames[i].split('_')[0]
            region_name = ''
            if map_name not in ["Dirtmouth", "Crossroads", "Greenpath", "Fungal",
                                "Fog", "Cliffs", "Crystal", "Basin", "Abyss",
                                "Grounds", "Edge", "City", "Hive", "Waterways",
                                "Deepnest", "Gardens", "Palace", "POP", "Egg",
                                "Grimm", "Dream", "Godhome"]:
                room_name_no_area = room_name
                map_name = room_name
            if room_name == 'Dirtmouth':
                room_name_no_area = room_name
            if map_name.split('_')[0] == "Invincible":
                map_name = "Godhome"
            if room_name in ['Black_Egg_Temple', 'Salubra']:
                map_name = "Crossroads"
                if room_name in 'Black_Egg_Temple':
                    region_name = 'Black_Egg'
            if room_name in ['Sly', 'Sly_Basement', 'Iselda', 'Bretta',
                             'Bretta_Basement', 'Jiji', 'Jinn']:
                map_name = "Dirtmouth"
            if map_name == 'Egg':
                room_name_no_area = room_name
                region_name = 'Black_Egg'
                map_name = 'Crossroads'
            if map_name == 'POP':
                region_name = map_name
                room_name_no_area = room_name
                map_name = 'Palace'
            if room_name == "King's_Pass":
                region_name = map_name
                map_name = 'Dirtmouth'

            # TODO: add region randomizer names
            if region_name == '':
                region_name = map_name

            locDict[oldNames[i]] = {}

            locDict[oldNames[i]]['name'] = room_name
            locDict[oldNames[i]]['short_name'] = room_name_no_area
            locDict[oldNames[i]]['map'] = map_name
            locDict[oldNames[i]]['area'] = region_name

        # Create JSON file
        addText('Creating JSON file.\n')
        with open(JSONPATH, "w") as outfile:
            json.dump(locDict, outfile, indent=4)


if __name__ == '__main__':
    '''Main program, defines main variables then begins loop'''

    # Create dictionary
    # TODO remove folder delete for release!
    # if os.path.isdir(INNERPATH):
    #     shutil.rmtree(INNERPATH)
    if not os.path.isdir(INNERPATH):
        os.mkdir(INNERPATH)

    running = True

    # Main window parameters
    root = tk.Tk()
    root.title('HKTranslator')

    # Frames to place widgets
    top = tk.Frame(root)
    mid = tk.Frame(root)
    checkboxes = tk.Frame(root)
    bot = tk.Frame(root)

    # Place frames in window
    top.pack()
    mid.pack()
    checkboxes.pack()
    bot.pack()

    # If config file exists, read it and check if any problems
    # If any problems or file is not there, create it
    configFile, configString = readConfig()

    # Buttons and text
    toggle_text = tk.StringVar(value='Pause translation')
    toggle_button = tk.Button(
        root, textvariable=toggle_text, command=toggleTrans)
    openFile_button = tk.Button(root, text='Open file', command=openFile)
    exit_button = tk.Button(root, text='Exit', command=root.quit)
    main_stext = st.ScrolledText(root, width=TEXT_WIDTH, height=TEXT_HEIGHT)

    # Place buttons and text
    toggle_button.pack(in_=top)
    openFile_button.pack(in_=mid, side=tk.LEFT)
    exit_button.pack(in_=mid, side=tk.LEFT)
    main_stext.pack(in_=bot)

    # Create checkboxes, probably not a good idea to do so automatically
    varnames = []
    checknames = []
    for i in range(len(SETTINGS)):
        varname = ''.join(list(map(lambda x: x[0], SETTINGS[i].split(' '))))
        varnames.append(varname)
        checkname = varname + '_check'
        checknames.append(checkname)
        globals()[varname] = tk.IntVar(value=configFile[i])
        checkText = SETTINGS[i].capitalize().replace(' reachable', '')
        globals()[checkname] = tk.Checkbutton(
            root, text=checkText, variable=globals()[varname])
        globals()[checkname].pack(in_=checkboxes)

    # Print config status
    addText(configString)

    # Create JSON dictionary
    # This is where all the region logic is
    # [IMPORTANT] This is very messy and I will maybe stop updating it...
    if os.path.isfile(GOODJSONPATH):
        json_to_read = GOODJSONPATH
    else:
        createJSON()
        json_to_read = JSONPATH

    # Create dictionary from JSON file
    translationDict = {}
    try:
        addText('Reading JSON file.\n')
        with open(json_to_read) as json_file:
            translationDict = json.load(json_file)
    except Exception as e:
        errorBoxQuit('Dictionary error. ' + str(e))

    allAreas = []
    for x in translationDict:
        if translationDict[x]['map'] not in allAreas:
            allAreas.append(translationDict[x]['map'])
    print(allAreas)

    # Start main function loop
    prevToWrite = ''
    addText('Translation started.')
    root.after(10, updateLoop)
    root.mainloop()

    # Write config when program is closed
    writeConfig()
