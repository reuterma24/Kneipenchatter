#24.26.2023
#by Arturo Bertoglia

import logging, time, os, queue, threading, sys
import PySimpleGUI as sg

#sg.theme_previewer()

#Logging
start_time = time.time()
logging_FilePath = os.getcwd()+'//main_log.txt'
logging.basicConfig(filename=logging_FilePath, filemode="w", encoding='utf-8', level=logging.DEBUG)
logging.info(start_time)
print("Script Start")
scriptName = "Kneipenchatter Deluxe v0.1"

#Constants
FILEPATH_LOGO = r"/home/arturo/Dokumente/HU-Berlin/4.SS/Peer2Peer/PapaTangoPapa/data/logo.png"
#[sg.Image(FILEPATH_LOGO, p=((250,0),(10,10)))]
BAR_LENGTH = 100
NICKNAME = "Alex"

# --------------------- RUNTIME ---------------------
def runtime(gui_queue, input_FilePath, output_FilePath):
  try:
    logging.info(f"Started processing \nInput File is: {input_FilePath}")
    print(f"Vorgang gestartet \nEingabedate befindet sich in: {input_FilePath}")

    gui_queue.put(0)    #Success
    return(0)

  except:
    logging.exception("Exception on runtime")
    print("Es gab einen Fehler während der Ausführung, bitte melden Sie sich bei dem IT Typ -Arturo Bertoglia")
    gui_queue.put(1)    #Error
    return(1)   #Further exceptions kinds have to be created as Exception  class and given an error code to be catched also in the GUI

  finally:
    #Export Data independet of success or error
    logging.info(f"Finished processing \nExporting Data to: {output_FilePath}")
    print(f"Vorgang beendet \nAusgabedatei wird gespeichert im: {output_FilePath}")

# --------------------- GUI ---------------------
def main_window():
  global NICKNAME
  gui_queue = queue.Queue()  # queue used to communicate between the gui and the threads
  
  layout = [
    [sg.Text(scriptName, s=30, justification="c", text_color="white", font=("Helvetica", 18))],
    [sg.Multiline(size=(60, 20), reroute_stdout=True, echo_stdout_stderr=True, disabled=True, autoscroll=True)],
    [sg.Text("Message Box: ", s=15, justification="r")],
    [sg.Input(s=(59,5), key="messageText"), sg.Button("Send",s=12 , key="messageEnter", bind_return_key=True)],
    [sg.Exit(button_text="Exit App", key="exit", s=16, button_color="tomato", pad=((40,0), (0,0))), sg.Button("Start App", s=16, key="start", button_color="green", tooltip="Let´s Go!"), sg.Button("Join Chat", s=16, key="join"), sg.Button("Leave Chat", s=16, key="leave",target=(1,1))],
    [sg.Input(NICKNAME, s=(18,1), key="nickname_Value", pad=((500,0),(0,0))), sg.Button("Change Nickname", s=16, key="nickname_Change")]
    ]

  window = sg.Window(scriptName, layout, use_custom_titlebar=False,no_titlebar=False ,size=(1000,720), grab_anywhere=True, finalize=True)
  window.bind("<Escape>", "_Escape")

  print(f"Welcome to {scriptName} we hope you enjoy your stay! \nYour current nickname is: {NICKNAME}")

  # --------------------- EVENT LOOP ---------------------
  while True: 
    event, values = window.read(timeout=100)
    #print(event, values)    #Debugging

    if event in ("exit", sg.WINDOW_CLOSED, "_Escape"):
      break

    if event == "start":
      window["start"].update(disabled=True)
      threading.Thread(target=runtime, kwargs={
        "gui_queue": gui_queue,
        }, 

        daemon=True).start()
    
    if event == "messageEnter":
      print(NICKNAME + ": " + values["messageText"])
      window["messageText"].update(value = "")

    if event == "nickname_Change":
      NICKNAME = values["nickname_Value"]
      print(f"Your nickname has been changed to: {NICKNAME}")

    
    # --------------- Check for incoming messages from threads  ---------------
    try:
      message = gui_queue.get_nowait()
    
      if message == 0:  #Success - Answer from thread depending on if we can just print the answer or have to check them from queue
        print("")

      if message == 1:  #All Errors
        sg.popup_error("Exception ocurred")
    
    except queue.Empty:             # get_nowait() will get exception when Queue is empty
      message = None              # break from the loop if no more messages are queued up

  window.close()

if __name__ == "__main__":
    theme = "DarkBlue"
    font_family = "Bahnschrift"
    font_size = 14
    sg.theme(theme)
    sg.set_options(font=(font_family, font_size))
    main_window()


#Logging
logging.info("--- %s seconds ---" % (time.time() - start_time))
print("--- %s seconds ---" % (time.time() - start_time))
print("Safe Exit")