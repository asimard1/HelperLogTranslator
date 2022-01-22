import tkinter as tk  # GUI
from tkinter import scrolledtext as st  # Text widget
from tkinter import messagebox as mb  # Error box
import os  # Check if files exist, create directory and find helperlog
import requests  # Download translator file if it doesn't exist
import datetime  # Print update time


# For text widget
TEXT_HEIGHT = 10
TEXT_WIDTH = 22
# Helper log paths
PATH = os.getenv('LOCALAPPDATA') + \
    'Low/Team Cherry/Hollow Knight/Randomizer 4/Recent/HelperLog.txt'
NEWPATH = os.getenv(
    'LOCALAPPDATA') + 'Low/Team Cherry/Hollow Knight/Randomizer 4/Recent/HelperLogTrans.txt'
# Path for files used by program
INNERPATH = 'createdFiles'
XMLURL = 'https://raw.githubusercontent.com/ManicJamie/HKTranslator/master/TranslatorDictionary.xml'
XMLPATH = INNERPATH + '/TranslatorDictionary.xml'
CONFIGPATH = INNERPATH + '/config.ini'
# All possible blocks in HelperLog.txt
SETTINGS = ['UNCHECKED REACHABLE LOCATIONS',
            'PREVIEWED LOCATIONS',
            'UNCHECKED REACHABLE TRANSITIONS',
            'CHECKED TRANSITIONS',
            'RESPAWNING ITEMS']


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
        main_stext.delete('1.0', '2.0')
    main_stext.insert(tk.INSERT, string)

    main_stext.config(state=tk.DISABLED)


def updateSettings():
    '''Gets which blocks to place in translated file from checkboxes'''
    tab = []
    for i in range(len(varnames)):
        if globals()[varnames[i]].get():
            tab.append(SETTINGS[i])

    return tab


def updateLoop():
    '''Main loop, repeats until window is closed'''
    global prevToWrite
    global toWrite

    if running:
        settingsTab = updateSettings()
        with open(PATH, 'r') as f:
            ogFile = f.read()

        blocks = ogFile.split('\n\n')

        toWrite = ''

        for block in blocks:
            if block.split('\n')[0] in settingsTab:
                toWrite += block + '\n\n'

        if toWrite != prevToWrite:
            # Update file
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            addText(f'\nUpdated at {current_time}.')

            with open(NEWPATH, 'w') as f:
                f.write(toWrite)

    prevToWrite = toWrite
    root.after(100, updateLoop)


def writeConfig():
    '''Writes config to file to save settings for the checkboxes'''
    string = ''
    for i in range(len(varnames)):
        string += str(globals()[varnames[i]].get())
    with open(CONFIGPATH, 'w') as f:
        f.write(string)


if __name__ == '__main__':
    '''Main program, defines main variables then begins loop'''

    if not os.path.isdir(INNERPATH):
        os.mkdir(INNERPATH)

    running = True

    root = tk.Tk()
    root.title('HKTranslator')

    top = tk.Frame(root)
    mid = tk.Frame(root)
    checkboxes = tk.Frame(root)
    bot = tk.Frame(root)

    top.pack()
    mid.pack()
    checkboxes.pack()
    bot.pack()

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

    toggle_text = tk.StringVar(value='Pause translation')

    toggle_button = tk.Button(
        root, textvariable=toggle_text, command=toggleTrans)
    openFile_button = tk.Button(root, text='Open file', command=openFile)
    exit_button = tk.Button(root, text='Exit', command=root.quit)
    main_stext = st.ScrolledText(root, width=TEXT_WIDTH, height=TEXT_HEIGHT)

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

    addText(configString)

    if not os.path.isfile(XMLPATH):
        addText('Downloading xml.\n')
        try:
            r = requests.get(XMLURL)
            open(XMLPATH, 'wb').write(r.content)
        except Exception:
            mb.showerror(
                title='Error', message='Could not download TranslatorDictionary.xml. ' +
                'Check your internet connection and try again or download manually.')
            quit()
    else:
        addText('Translator found.\n')

    addText('Translation started.')

    prevToWrite = ''

    root.after(10, updateLoop)
    root.mainloop()
    writeConfig()
