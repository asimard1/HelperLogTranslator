import tkinter as tk  # GUI
from tkinter import scrolledtext as st  # Text widget
from tkinter import messagebox as mb  # Error box
import requests  # Get translator from github
import os  # Check if files exist, create directory and find helperlog
import datetime  # Print update time
import json  # To read dictionary


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
CONFIGPATH = INNERPATH + '/config.ini'
XMLPATH = INNERPATH + '/mapDict.xml'
XMLURL = 'https://raw.githubusercontent.com/ManicJamie/HKTranslator/master/TranslatorDictionary.xml'
# All possible blocks in HelperLog.txt
SETTINGS = ['UNCHECKED REACHABLE LOCATIONS',
            'PREVIEWED LOCATIONS',
            'UNCHECKED REACHABLE TRANSITIONS',
            'CHECKED TRANSITIONS',
            'RESPAWNING ITEMS']


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
    '''Gets which blocks to place in translated file from checkboxes'''
    tab = []
    for i in range(len(varnames)):
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

        # Replace room names
        for word in translationDict:
            helperLog = helperLog.replace(word, translationDict[word])

        blocks = helperLog.split('\n\n')
        toWrite = ''

        for block in blocks:
            # Add only wanted blocks
            if block.split('\n')[0] in settingsTab:
                toWrite += block + '\n\n'

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


if __name__ == '__main__':
    '''Main program, defines main variables then begins loop'''

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
    if os.path.isfile(CONFIGPATH):
        with open(CONFIGPATH, 'r') as f:
            configFile = f.read()
        if len(configFile) == len(SETTINGS):
            configString = 'Config.ini found.\n'
        else:
            configString = 'Config size error.\nConfig.ini created.\n'
            configFile = '1' * len(SETTINGS)
    else:
        configFile = '1' * len(SETTINGS)
        configString = 'Config.ini created.\n'

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

    # Read json, or create it
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
        for i in range(len(oldNames)):
            locDict[oldNames[i]] = newNames[i]

        # Create JSON file
        addText('Creating JSON file.\n')
        with open(JSONPATH, "w") as outfile:
            json.dump(locDict, outfile, indent=4)

    # Create dictionary from JSON file
    translationDict = {}
    try:
        addText('Reading JSON file.\n')
        with open(JSONPATH) as json_file:
            translationDict = json.load(json_file)
    except Exception as e:
        errorBoxQuit('Dictionary error. ' + str(e))

    # Start main function loop
    prevToWrite = ''
    addText('Translation started.')
    root.after(10, updateLoop)
    root.mainloop()

    # Write config when program is closed
    writeConfig()
