#24.26.2023
#Starte mit extra Port Argumente für Bootstrapping

import logging, time, os, queue, threading, sys
import PySimpleGUI as sg
from chat_protocol import ChatProtocol, Util
from protocol import KademliaProtocol
from random import randrange

#Logging
start_time = time.time()
logging_FilePath = os.getcwd()+'//main_log.txt'
logging.basicConfig(filename=logging_FilePath, filemode="w", encoding='utf-8', level=logging.DEBUG)
logging.info(start_time)
print("Script Start")
scriptName = "Kneipenchatter Deluxe v0.1"

#Constants
#FILEPATH_LOGO = r"/home/arturo/Dokumente/HU-Berlin/4.SS/Peer2Peer/PapaTangoPapa/data/logo.png"
#[sg.Image(FILEPATH_LOGO, p=((250,0),(10,10)))]
BAR_LENGTH = 100
NICKNAME = None
GUI_QUEUE = queue.Queue()  # queue used to communicate between the app and the gui
APP_QUEUE = queue.Queue()  # queue used to communicate between the gui and the app
PORT  = int(sys.argv[1])   #Starte manuell mit extra Port para

class ChatApp:
    def __init__(self, user_alias, port):
        self.port = port
        self.chat_protocol = ChatProtocol(user_alias, port)
        self.kademlia = KademliaProtocol(port)

    def create_chat_room(self, chat_room_name, number_of_peers):
        peers = list(self.kademlia.sourceNode.find_node(self.kademlia.sourceNode.id).values())[:number_of_peers]
        id = Util.create_random_session_id()
        self.chat_protocol.send_session_creation(id, chat_room_name, peers)

    def leave_chat_room(self, chat_room_id):
        self.chat_protocol.send_leave_session(chat_room_id)

    def join_chat_room(self):
        peers = list(self.kademlia.sourceNode.find_node(self.kademlia.sourceNode.id).values())
        self.chat_protocol.send_join_session(peers)

    def send_message(self, session_id, msg):
        self.chat_protocol.send_msg(session_id, msg)

    def get_messages(self, session_id, number_of_messages):
        Util.get_messages(session_id, number_of_messages)


# --------------------- RUNTIME ---------------------
def runtime():
  global NICKNAME, PORT, GUI_QUEUE, APP_QUEUE

  try:
    logging.info(f"Started protocol with values: \nNickname : {NICKNAME} \nPort : {PORT}")
    #print(f"Started protocol with values: \nNickname : {NICKNAME} \nPort : {PORT}")
    app = ChatApp(NICKNAME, PORT)
    
    while True:
      try:
        if app.session_id: #Here we check for the Session ID Property of the app. If we are not in a chat room it would be none
          time.sleep(1) #To avoid it overloading
          for msg in ChatApp.get_messages(session_id=app.session_id, number_of_messages=10):
            print(msg)
      except:
        logging.warning("Exception while getting messages")

      try:
        message = APP_QUEUE.get()
        code = str(message).split(":", 1)[0]
        text = str(message).split(":", 1)[1]
        logging.info(f"Code:{code} \nText:{text}")

        if code == "MS":
          print(f"{NICKNAME} : {text}")
          app.send_message(session_id=app.session_id, msg=text)
           
        if code == "CG":
          chat_room_name = str(randrange(0,999999))
          print(f"Creating a Chat Room named {chat_room_name} for {text} peers")
          app.create_chat_room(chat_room_name=chat_room_name, number_of_peers=text)
        
        if code == "JG":
          print("Joining a Chat Room")
          app.join_chat_room()

        if code == "LG":
          print("Leaving a Chat Room")
          app.leave_chat_room(chat_room_id=app.session_id)

      except queue.Empty:
         message = None
         
    GUI_QUEUE.put(0)    #Success
    return(0)

  except:
    logging.exception("Exception on runtime")
    print("There was an exception while running the protocol")
    GUI_QUEUE.put(1)    #Error
    return(1)

  finally:
    #Export Data independet of success or error
    logging.info(f"Protocol is shutting down")
    print(f"Protocol is shutting down")

# --------------------- GUI ---------------------
def main_window():
  global NICKNAME, PORT, GUI_QUEUE, APP_QUEUE
  
  layout = [
    [sg.Text(scriptName, s=30, justification="c", text_color="white", font=("Helvetica", 18))],
    [sg.Multiline(size=(60, 20), reroute_stdout=True, echo_stdout_stderr=True, disabled=True, autoscroll=True)],
    [sg.Text("Message Box: ", s=15, justification="r")],
    [sg.Input(s=(59,5), key="messageText", disabled=True), sg.Button("Send",s=12 , key="messageEnter", bind_return_key=True, disabled=True)],
    [sg.Exit(button_text="Exit App", key="exit", s=16, button_color="tomato", pad=((40,0), (0,0))), sg.Button("Create Chatroom", s=16, key="create", button_color="green", tooltip="Initializes Protocol"), sg.Button("Join Chat", s=16, key="join"), sg.Button("Leave Chat", s=16, key="leave", disabled=True)]
    ]
  
  window = sg.Window(scriptName, layout, use_custom_titlebar=False,no_titlebar=False ,size=(1000,720), grab_anywhere=True, finalize=True)
  window.bind("<Escape>", "_Escape")

  print(f"Welcome to {scriptName} we hope you enjoy your stay!")

  # --------------------- EVENT LOOP ---------------------
  while True: 
    event, values = window.read(timeout=100)
    #print(event, values)    #Debugging

    if event in ("exit", sg.WINDOW_CLOSED, "_Escape"):
      break

    if NICKNAME == None:  #So this is the first thing Happening, a pop-up window that will block everything until a nickname is given
      NICKNAME = sg.popup_get_text(message="Please enter your Nickname", title="Nickname Setup")
      print(f"Your current nickname is: {NICKNAME}")

    if len(threading.enumerate()) < 2 and NICKNAME != None:  #Once a nickname is given we initialize the protocol. This will also keep spawning the protocol if that thread somehow gets killed.
      threading.Thread(target=runtime, daemon=True).start()
    
    if event == "create":
      window["create"].update(disabled=True)
      window["join"].update(disabled=True)
      window["leave"].update(disabled=False)
      window["messageText"].update(disabled=False)
      window["messageEnter"].update(disabled=False)

      number_of_peers = sg.popup_get_text(message="How many peers should be allowed in the room?", title="Number of Peers")
      APP_QUEUE.put(f"CG: {number_of_peers}")

    if event == "join":
      window["create"].update(disabled=True)
      window["join"].update(disabled=True)
      window["leave"].update(disabled=False)
      window["messageText"].update(disabled=False)
      window["messageEnter"].update(disabled=False)

      APP_QUEUE.put("JG:" + "1")

    if event == "leave":
      window["create"].update(disabled=False)
      window["join"].update(disabled=False)
      window["leave"].update(disabled=True)
      window["messageText"].update(disabled=True)
      window["messageEnter"].update(disabled=True)
      APP_QUEUE.put("LG:" + "1")

    if event == "messageEnter":
      APP_QUEUE.put("MS:" + (values["messageText"]))
      window["messageText"].update(value = "")

    # --------------- Check for incoming messages from threads  ---------------
    try:
      message = GUI_QUEUE.get_nowait()
      if message == 0:  #Success - Answer from thread depending on if we can just print the answer or have to check them from queue
        print("Protocol closed succesfully")

      if message == 1:  #All Errors
        sg.popup_error("Exception ocurred on Protocol")
    
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