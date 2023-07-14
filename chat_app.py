# 24.26.2023
# Starte mit extra Port Argumente für Bootstrapping

import logging, os, queue, threading, sys, datetime, time
import PySimpleGUI as sg
from chat_protocol import ChatProtocol, Util
from protocol import KademliaProtocol
from random import randrange

# Constants
NICKNAME = None
NODE_ID = None
SESSION_ID = None
GUI_QUEUE = queue.Queue()  # queue used to communicate between the app and the gui
APP_QUEUE = queue.Queue()  # queue used to communicate between the gui and the app
PORT = int(sys.argv[1])  # Starte manuell mit extra Port para

# Logging
scriptName = "Kneipenchatter Deluxe v0.1"
start_time = datetime.datetime.now().strftime(r"%m/%d/%Y, %H:%M:%S")
logging_FilePath = f"{os.getcwd()}//main_log_{PORT}.txt"
logging.basicConfig(filename=logging_FilePath, filemode="w", encoding='utf-8', level=logging.DEBUG)
logging.info(f"{scriptName}\n{start_time}")
print("Script Start")


class ChatApp:
    def __init__(self, user_alias, port):
        self.port = port
        self.chat_protocol = ChatProtocol(user_alias, port)
        self.kademlia = KademliaProtocol(port)

    def create_chat_room(self, chat_room_name, number_of_peers):
        peers = list(self.kademlia.sourceNode.find_node(self.kademlia.sourceNode.id).values())[:number_of_peers]
        id = Util.create_random_session_id()
        self.chat_protocol.send_session_creation(id, chat_room_name, peers)

    def leave_chat_room(self):
        id = self.get_single_session_id()
        self.chat_protocol.send_leave_session(id)

    def join_chat_room(self):
        peers = list(self.kademlia.sourceNode.find_node(self.kademlia.sourceNode.id).values())
        self.chat_protocol.send_join_session(peers)

    def send_message(self, msg):
        id = self.get_single_session_id()
        self.chat_protocol.send_msg(id, msg)

    def get_messages(self, number_of_messages):
        id = self.get_single_session_id()
        return Util.get_messages(id, number_of_messages)

    # This is used for demonstration purposes. We do not support multiple sessions in the frontend yet.
    @staticmethod
    def get_single_session_id():
        ids = Util.get_session_ids()
        if len(ids) > 0:
            return ids[0]
        else:
            return None

# --------------------- RUNTIME ---------------------
def runtime():
    global NICKNAME, PORT, GUI_QUEUE, APP_QUEUE, NODE_ID, SESSION_ID

    try:
        logging.info(f"Started protocol with values: \n\tNickname : {NICKNAME} \n\tPort : {PORT}")
        app = ChatApp(NICKNAME, PORT)
        messages_old = []   #Messages Starter
        NODE_ID = app.kademlia.sourceNode.id
        GUI_QUEUE.put(f"NI:{NODE_ID}")  #Actualizes Node ID in GUI

        while True:
            
            if app.get_single_session_id():  # Here we check for the Session ID Property of the app. If we are not in a chat room it would be none. This could control the GUI as well
                SESSION_ID = app.get_single_session_id()
                GUI_QUEUE.put(f"SI:{SESSION_ID}")   #Actualize Session ID in GUI
                logging.debug("Got a Session ID")
                time.sleep(1)  # To avoid it overloading

                messages_new =  app.get_messages(number_of_messages=10) #Get list of dicts with keys timestamp, msg, user_alias, hash
                messages_diff = [x for x in messages_new if x not in messages_old]  #Check New against Old
                
                for entry in messages_diff:
                    converted_ticks = datetime.datetime.now() + datetime.timedelta(microseconds = entry["timestamp"]/10)
                    print(converted_ticks.strftime(r"%m/%d/%Y, %H:%M:%S") + " " + entry["user_alias"] + " : " + entry["msg"])
                    messages_old.append(entry) #Update Old list

            else:
                logging.warning("No Session ID")
                SESSION_ID = None
                GUI_QUEUE.put(f"SI:{SESSION_ID}")   #Empty Session ID in GUI

            try:
                message = APP_QUEUE.get(timeout=1)      #Maybe change to getnowait and see what happens
                code, text = str(message).split(":", 1)
                logging.info(f"\n\tCode:{code} \n\tText:{text}")

                if code == "MS":
                    logging.info(f"\tsend_message {text}")
                    app.send_message(msg=text)

                if code == "CG":
                    chat_room_name = str(randrange(0, 999999))
                    print(f"Creating a Chat Room named {chat_room_name} for {text} peers")
                    app.create_chat_room(chat_room_name=chat_room_name, number_of_peers=int(text))

                if code == "JG":
                    print("Joining a Chat Room")
                    app.join_chat_room()

                if code == "LG":
                    print("Leaving a Chat Room")
                    app.leave_chat_room()

            except queue.Empty:
                message = None

    except:
        logging.exception("Exception on runtime")
        print("There was an exception while running the protocol")
        GUI_QUEUE.put("EC:1")  # Error
        return ("EC:1")

    finally:
        # Export Data independet of success or error
        logging.info(f"Protocol is shutting down")
        print(f"Protocol is shutting down")


# --------------------- GUI ---------------------
def main_window():
    global NICKNAME, PORT, GUI_QUEUE, APP_QUEUE, NODE_ID

    layout = [
        [sg.Text(scriptName, s=35, justification="l", text_color="white", font=("Helvetica", 18)), 
         sg.Text(f"Nickname: {NICKNAME}", s=30, justification="c", key="name", text_color="black", background_color="white")], 
        [sg.Text(f"Port: {PORT}", s=12, justification="c", key="port", text_color="black", background_color="white"),
        sg.Text(f"Node ID: {NODE_ID}", s=16, justification="c", key="node_id", text_color="black", background_color="white"),
        sg.Text(f"Session ID: {SESSION_ID}", s=48, justification="c", key="session_id", text_color="black", background_color="white")],
        [sg.Multiline(size=(60, 20), reroute_stdout=True, echo_stdout_stderr=True, disabled=True, autoscroll=True)],
        [sg.Text("Message Box: ", s=15, justification="r")],
        [sg.Input(s=(59, 5), key="messageText", disabled=True),
         sg.Button("Send", s=12, key="messageEnter", bind_return_key=True, disabled=True)],
        [sg.Exit(button_text="Exit App", key="exit", s=16, button_color="tomato", pad=((40, 0), (0, 0))),
         sg.Button("Create Chatroom", s=16, key="create", button_color="green", tooltip="Initializes Protocol"),
         sg.Button("Join Chat", s=16, key="join"), sg.Button("Leave Chat", s=16, key="leave", disabled=True)]
    ]

    window = sg.Window(scriptName, layout, use_custom_titlebar=False, no_titlebar=False, size=(1000, 720),
                       grab_anywhere=True, finalize=True, resizable=True)
    window.bind("<Escape>", "_Escape")

    print(f"Welcome to {scriptName} we hope you enjoy your stay!")

    # --------------------- EVENT LOOP ---------------------
    while True:
        event, values = window.read(timeout=100)
        # print(event, values)    #Debugging

        if event in ("exit", sg.WINDOW_CLOSED, "_Escape"):
            break

        if NICKNAME == None:  # So this is the first thing Happening, a pop-up window that will block everything until a nickname is given
            NICKNAME = sg.popup_get_text(message="Please enter your Nickname", title="Nickname Setup")
            print(f"Your current nickname is: {NICKNAME}")

        if len(threading.enumerate()) < 2 and NICKNAME != None:  # Once a nickname is given we initialize the protocol. This will also keep spawning the protocol if that thread somehow gets killed.
            threading.Thread(target=runtime, daemon=True).start()
            window["name"].update(value=f"Nickname: {NICKNAME}")

        if event == "create":
            number_of_peers = sg.popup_get_text(message="How many of you closest peers do you want to ask?",
                                                title="Number of Peers")
            APP_QUEUE.put(f"CG: {number_of_peers}")

        if event == "join":
            APP_QUEUE.put("JG:" + "1")

        if event == "leave":
            APP_QUEUE.put("LG:" + "1")

        if event == "messageEnter":
            APP_QUEUE.put("MS:" + (values["messageText"]))
            window["messageText"].update(value="")

        # --------------- Check for incoming messages from threads  ---------------
        try:
            message = GUI_QUEUE.get_nowait()
            code, text = str(message).split(":", 1)
            logging.info(f"\n\tCode:{code} \n\tText:{text}")
            
            if code == "NI":     #Node ID
                window["node_id"].update(value=f"Node ID: {NODE_ID}")

            if code == "SI":     #Session ID    I
                window["session_id"].update(value=f"Session ID: {SESSION_ID}")  #This is just to always update the ID in the GUI

                if SESSION_ID != None:  #Logic for success/we are in a chat group
                    window["create"].update(disabled=True)
                    window["join"].update(disabled=True)
                    window["leave"].update(disabled=False)
                    window["messageText"].update(disabled=False)
                    window["messageEnter"].update(disabled=False)
                else:           #Logic for failure/we are not in a chat group
                    window["create"].update(disabled=False)
                    window["join"].update(disabled=False)
                    window["leave"].update(disabled=True)
                    window["messageText"].update(disabled=True)
                    window["messageEnter"].update(disabled=True)


            if code == "EC":  # All Errors
                sg.popup_error("Exception ocurred on Protocol")
                break   #Avoid that crazy loop

        except queue.Empty:  # get_nowait() will get exception when Queue is empty
            message = None  # break from the loop if no more messages are queued up

    window.close()


if __name__ == "__main__":
    theme = "DarkBlue"
    font_family = "Bahnschrift"
    font_size = 14
    sg.theme(theme)
    sg.set_options(font=(font_family, font_size))
    main_window()

# Logging
end_time = datetime.datetime.now().strftime(r"%m/%d/%Y, %H:%M:%S")
logging.info(f"{scriptName}\n{end_time}")
print("Safe Exit")