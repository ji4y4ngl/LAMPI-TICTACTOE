import platform
from kivy.app import App
from kivy.properties import NumericProperty, AliasProperty, BooleanProperty
from kivy.uix.screenmanager import NoTransition
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from math import fabs
import json
from paho.mqtt.client import Client
import pigpio
from lamp_common import *
import lampi.lampi_util
import random

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

MQTT_CLIENT_ID = "lamp_ui"
GAME_CLIENT_ID = "game_ui"
sm = ScreenManager(transition=NoTransition())
mqtt = Client(client_id=MQTT_CLIENT_ID)
players_turn = 'None'
device_id = lampi.lampi_util.get_device_id()

def create_game_code():
    letters = ['x', 'y', 'a', 'b']
    return ''.join(random.choice(letters) for i in range(3))

class LampScreen(Screen):
    pass

# --------------------------------------------------------------------
class StartScreen(Screen):
    associated_player2 = 'None'
    game_association_code = create_game_code()
    # game_state = [[0, 0, 0],
    #               [0, 0, 0],
    #               [0, 0, 0]]
    device_associated_to_game = BooleanProperty(True)
    game_mqtt_client = Client(client_id=GAME_CLIENT_ID)

    def __init__(self, **kwargs):
        super(StartScreen, self).__init__(**kwargs)
        self.game_mqtt_client.connect(MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
        self.game_mqtt_client.loop_start()
        self.game_mqtt_client.on_publish = self.on_publish
        self.game_mqtt_client.on_connect = self.on_connect

        self._associated_to_game = True
        
        self.create_popup = self._build_create_popup()
        self.create_popup.bind(on_open=self.update_create_popup)
        Clock.schedule_interval(self._poll_associated, 0.1)

    def on_connect(self, client, userdata, flags, rc):
        # self.game_mqtt_client.message_callback_add(TTT_TOPIC_GAME_CHANGE,
        #                                self.receive_new_game_state)
        self.game_mqtt_client.message_callback_add(TTT_TOPIC_ASSOCIATE,
                                        self.receive_associated_game)
        # self.game_mqtt_client.subscribe(TTT_TOPIC_GAME_CHANGE, qos=1)
        self.game_mqtt_client.subscribe(TTT_TOPIC_ASSOCIATE, qos=1)

    # def on_pre_enter(self):

    def on_publish(self, client, userdata, mid):
        print("Message published with mid:", mid)
    
    def _poll_associated(self, dt):
        # this polling loop allows us to synchronize changes from the
        #  MQTT callbacks (which happen in a different thread) to the
        #  Kivy UI
        self.device_associated_to_game = self._associated_to_game

    def receive_associated_game(self, client, userdata, message):
        new_associated = json.loads(message.payload.decode('utf-8'))
        # if self.associated_player2 != new_associated['player2']:
        #     if 'None' is not new_associated['player2']:
        #         self.game_association_code = new_associated['a_code']
        #         self._associated_to_game = True
        #     else:
        #         self._associated_to_game = False
    
    def on_device_associated_to_game(self, instance, value):
        if value:
            self.create_popup.dismiss()
        else:
            self.create_popup.open()
    
    def display_popup(self, btn):
        if self.ids.join == btn:
            sm.current = 'game'
        elif self.ids.create == btn:
            self.create_popup.open()

    def on_create_popup(self, instance, value):
        if value:
            self.create_popup.dismiss()
        else:
            self.create_popup.open()

    def _build_create_popup(self):
        code = self.game_association_code
        print(code)
        
        msg = {'player1': device_id,
            'player2': self.associated_player2,
            'a_code': self.game_association_code,
            'client': GAME_CLIENT_ID}
        self.game_mqtt_client.publish(TTT_TOPIC_ASSOCIATE,
                        json.dumps(msg).encode('utf-8'),
                        qos=1)
        self._publish_clock = None

        return Popup(title='Game Association Code',
                     content=Label(text='Msg here',
                                   font_size='20sp', color='yellow', halign='center'),
                     size_hint=(.8, .75), auto_dismiss=False)
    
    def update_create_popup(self, instance):
        code = self.game_association_code
        print(code)

        # player2 = self.associated_player2
        instance.content.text = ("Association Code:\n"
                                 f"{code}\n"
                                 "\n"
                                 "Send this to\n"
                                 "friend!\n")

    def receive_new_game_state(self, client, userdata, message):
        new_state = json.loads(message.payload.decode('utf-8'))
        # Clock.schedule_once(lambda dt: self._update_game_state(new_state), 0.01)

    def _update_game_state(self, new_state):
        self.game_state = new_state

        # if self._updated and new_state['client'] == MQTT_CLIENT_ID:
        #     # ignore updates generated by this client, except the first to
        #     #   make sure the UI is syncrhonized with the lamp_service
        #     return
        # self._updatingUI = True
        # try:
        #     if 'color' in new_state:
        #         self.hue = new_state['color']['h']
        #         self.saturation = new_state['color']['s']
        #     if 'brightness' in new_state:
        #         self.brightness = new_state['brightness']
        #     if 'on' in new_state:
        #         self.lamp_is_on = new_state['on']
        # finally:
        #     self._updatingUI = False

        # self._updated = True

class JoinScreen(Screen):
    # sm.add_widget(LampiApp(_updated = _updated))

    def on_game_connect(self):
        print("connected")
        
class GameScreen(Screen):
    turn = "X"
    winner = False
    X_win = 0
    O_win = 0
    game_state = [[0, 0, 0],
                  [0, 0, 0],
                  [0, 0, 0]]
    
    #state variables for ttt game only
    game_on = False
    prev_game_screen = 'start'
    
    game_mqtt_client = Client(client_id=GAME_CLIENT_ID)

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.game_mqtt_client.connect(MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
        self.game_mqtt_client.enable_logger()
        self.game_mqtt_client.on_connect = self.on_connect
        self.game_mqtt_client.loop_start()
        self.game_mqtt_client.on_publish = self.on_publish

    def on_publish(self, client, userdata, mid):
        print("Message published with mid:", mid)
        
    def publish_game_state(self):
        msg = {'turn': self.turn,
               'game_state': self.game_state,
               'client': GAME_CLIENT_ID}
        game_state_json = json.dumps(msg).encode('utf-8')
        self.game_mqtt_client.publish(TTT_TOPIC_SET_CONFIG, game_state_json, qos = 1)
        print("new state published", game_state_json)
    
    def on_connect(self, client, userdata, flags, rc):
        self.game_mqtt_client.publish(client_state_topic(GAME_CLIENT_ID), b"1",
                                      qos=2, retain=True)
        self.game_mqtt_client.message_callback_add(TTT_TOPIC_GAME_CHANGE,
                                       self.receive_new_lamp_state)
        self.game_mqtt_client.message_callback_add(broker_bridge_connection_topic(),
                                       self.receive_bridge_connection_status)
        # self.mqtt.message_callback_add(TOPIC_LAMP_ASSOCIATED,
        #                                self.receive_associated)
        self.game_mqtt_client.subscribe(broker_bridge_connection_topic(), qos=1)
        self.game_mqtt_client.subscribe(TTT_TOPIC_GAME_CHANGE, qos=1)
        # self.mqtt.subscribe(TOPIC_LAMP_ASSOCIATED, qos=2)

    def receive_new_game_state(self, client, userdata, message):
        new_game_state = json.loads(message.payload.decode('utf-8'))
        # Clock.schedule_once(lambda dt: self._update_ui(new_game_state), 0.01)

    def no_winner(self):
        if self.winner == False and all(all(cell != 0 for cell in row) for row in self.game_state):
            self.ids.score.text = "IT'S A TIE!!"

        # End The Game
    def end_game(self, a, b, c):
        self.winner = True
        a.color = "red"
        b.color = "red"
        c.color = "red"

        # Disable the buttons
        self.disable_all_buttons(True)
        # Set Label for winner
        self.ids.score.text = f"{a.text} Wins!"

        # Keep track of winners and loser
        if a.text == "X":
            self.X_win +=1
        else:
            self.O_win +=1

        self.ids.game.text = f"X Wins: {self.X_win}  |  O Wins: {self.O_win}"

    def disable_all_buttons(self, BooleanProperty):
        for row in range(3):
            for col in range(3):
                btn_id = f"btn{row * 3 + col + 1}"
                self.ids[btn_id].disabled = BooleanProperty

    def win(self):
        for row in range(3):
            if self.game_state[row][0] == self.game_state[row][1] == self.game_state[row][2] != 0:
                # If all cells in a row are equal and not empty, it's a win
                # self.end_game(self.ids[f"btn{self.game_state[row][0]}"], self.ids[f"btn{self.game_state[row][1]}"], self.ids[f"btn{self.game_state[row][2]}"])
                self.end_game(self.ids[f"btn{row * 3 + 1}"], self.ids[f"btn{row * 3 + 2}"], self.ids[f"btn{row * 3  + 3}"])

        for col in range(3):
            if self.game_state[0][col] == self.game_state[1][col] == self.game_state[2][col] != 0:
                # If all cells in a column are equal and not empty, it's a win
                self.end_game(self.ids[f"btn{0*3 + col+1}"], self.ids[f"btn{1*3 + col+1}"], self.ids[f"btn{2*3 + col+1}"])

        if self.game_state[0][0] != 0 and self.game_state[0][0] == self.game_state[1][1] == self.game_state[2][2]:
            #self.end_game(self.ids[f"btn{self.game_state[0][0]}"], self.ids[f"btn{self.game_state[1][1]}"], self.ids[f"btn{self.game_state[2][2]}"])
            self.end_game(self.ids[f"btn{0*3 + 0+1}"], self.ids[f"btn{1*3 + 1+1}"], self.ids[f"btn{2*3 + 2+1}"])
        
        if self.game_state[0][2] != 0 and self.game_state[0][2] == self.game_state[1][1] == self.game_state[2][0]:
            #self.end_game(self.ids[f"btn{self.game_state[0][2]}"], self.ids[f"btn{self.game_state[1][1]}"], self.ids[f"btn{self.game_state[2][0]}"])
            self.end_game(self.ids[f"btn{0*3 + 2+1}"], self.ids[f"btn{1*3 + 1+1}"], self.ids[f"btn{2*3 + 0+1}"])
        self.no_winner()

    def presser(self, btn):
        # print(btn.numid)
        # print(type(btn.numid))
        if btn.text == "":
            if self.turn == 'X':
                btn.text = "X"
                row = (int(btn.numid) - 1) // 3
                col = (int(btn.numid) - 1) % 3
                print("player1", row, col)
                print('game state1', self.game_state)
                self.game_state[row][col] = 1
                self.publish_game_state()
                print('game state2', self.game_state)
                self.ids.score.text = "O's Turn!"
                self.turn = "O"
            else:
                btn.text = "O"
                row = (int(btn.numid) - 1) // 3
                col = (int(btn.numid) - 1) % 3
                print("player2", row, col)
                print('game state1', self.game_state)
                self.game_state[row][col] = 2
                self.publish_game_state()
                print('game state2', self.game_state)
                self.ids.score.text = "X's Turn!"
                self.turn = "X"

        # Check To See if won
        self.win()

    def restart(self):
        self.turn = "X"
        self.winner = False
        self.game_state = [[0, 0, 0],
                           [0, 0, 0],
                           [0, 0, 0]]
        self.publish_game_state()
        # Enable The Buttons
        for row in range(3):
            for col in range(3):
                btn_id = f"btn{row * 3 + col + 1}"
                self.ids[btn_id].disabled = False
                self.ids[btn_id].text = ""
                self.ids[btn_id].color = "white"

        # Reset The Score Label
        self.ids.score.text = "X GOES FIRST!"

        # Reset The Winner Variable
        self.winner = False

    def exit_game(self):
        sm.current = 'start'
        # refresh state ************************************

# -----------------------------------------------------------------------------


class LampiApp(App):

    def build(self):
        sm.add_widget(LampScreen(name='lamp'))
        sm.add_widget(StartScreen(name='start'))
        sm.add_widget(JoinScreen(name='join'))
        sm.add_widget(GameScreen(name='game'))
        sm.current = 'lamp'
        print(sm.screen_names)

        return sm

    lamp_is_on = BooleanProperty()
    _updated = False
    _updatingUI = False
    _hue = NumericProperty()
    _saturation = NumericProperty()
    _brightness = NumericProperty()

    def _get_hue(self):
        return self._hue

    def _set_hue(self, value):
        self._hue = value

    def _get_saturation(self):
        return self._saturation

    def _set_saturation(self, value):
        self._saturation = value

    def _get_brightness(self):
        return self._brightness

    def _set_brightness(self, value):
        self._brightness = value

    hue = AliasProperty(_get_hue, _set_hue, bind=['_hue'])
    saturation = AliasProperty(_get_saturation, _set_saturation,
                               bind=['_saturation'])
    brightness = AliasProperty(_get_brightness, _set_brightness,
                               bind=['_brightness'])
    gpio17_pressed = BooleanProperty(False)
    gpio22_pressed = BooleanProperty(False)
    device_associated = BooleanProperty(True)
    
    #state variables for ttt game only
    game_on = False
    prev_game_screen = 'start'
    players_turn = 'n'

    def on_start(self):
        self._publish_clock = None
        self.mqtt_broker_bridged = False
        self._associated = True
        self.association_code = None
        self.mqtt = Client(client_id=MQTT_CLIENT_ID)
        self.mqtt.enable_logger()
        self.mqtt.will_set(client_state_topic(MQTT_CLIENT_ID), "0",
                           qos=2, retain=True)
        self.mqtt.on_connect = self.on_connect
        self.mqtt.connect(MQTT_BROKER_HOST, port=MQTT_BROKER_PORT,
                          keepalive=MQTT_BROKER_KEEP_ALIVE_SECS)
        self.mqtt.loop_start()
        self.associated_status_popup = self._build_associated_status_popup()
        self.associated_status_popup.bind(on_open=self.update_popup_associated)
        Clock.schedule_interval(self._poll_associated, 0.1)
        self.set_up_GPIO_and_device_status_popup()

    def _build_associated_status_popup(self):
        return Popup(title='Associate your Lamp',
                     content=Label(text='Msg here', font_size='30sp'),
                     size_hint=(1, 1), auto_dismiss=False)

    def on_hue(self, instance, value):
        if self._updatingUI:
            return
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_saturation(self, instance, value):
        if self._updatingUI:
            return
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_brightness(self, instance, value):
        if self._updatingUI:
            return
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_lamp_is_on(self, instance, value):
        if self._updatingUI:
            return
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_connect(self, client, userdata, flags, rc):
        self.mqtt.publish(client_state_topic(MQTT_CLIENT_ID), b"1",
                          qos=2, retain=True)
        self.mqtt.message_callback_add(TOPIC_LAMP_CHANGE_NOTIFICATION,
                                       self.receive_new_lamp_state)
        self.mqtt.message_callback_add(broker_bridge_connection_topic(),
                                       self.receive_bridge_connection_status)
        self.mqtt.message_callback_add(TOPIC_LAMP_ASSOCIATED,
                                       self.receive_associated)
        self.mqtt.subscribe(broker_bridge_connection_topic(), qos=1)
        self.mqtt.subscribe(TOPIC_LAMP_CHANGE_NOTIFICATION, qos=1)
        self.mqtt.subscribe(TOPIC_LAMP_ASSOCIATED, qos=2)

    def _poll_associated(self, dt):
        # this polling loop allows us to synchronize changes from the
        #  MQTT callbacks (which happen in a different thread) to the
        #  Kivy UI
        self.device_associated = self._associated

    def receive_associated(self, client, userdata, message):
        # this is called in MQTT event loop thread
        new_associated = json.loads(message.payload.decode('utf-8'))
        if self._associated != new_associated['associated']:
            if not new_associated['associated']:
                self.association_code = new_associated['code']
            else:
                self.association_code = None
            self._associated = new_associated['associated']

    def on_device_associated(self, instance, value):
        if value:
            self.associated_status_popup.dismiss()
        else:
            self.associated_status_popup.open()

    def update_popup_associated(self, instance):
        code = self.association_code[0:6]
        instance.content.text = ("Please use the\n"
                                 "following code\n"
                                 "to associate\n"
                                 "your device\n"
                                 "on the Web\n{}".format(code)
                                 )

    def receive_bridge_connection_status(self, client, userdata, message):
        # monitor if the MQTT bridge to our cloud broker is up
        if message.payload == b"1":
            self.mqtt_broker_bridged = True
        else:
            self.mqtt_broker_bridged = False

    def receive_new_lamp_state(self, client, userdata, message):
        new_state = json.loads(message.payload.decode('utf-8'))
        Clock.schedule_once(lambda dt: self._update_ui(new_state), 0.01)

    def _update_ui(self, new_state):
        if self._updated and new_state['client'] == MQTT_CLIENT_ID:
            # ignore updates generated by this client, except the first to
            #   make sure the UI is syncrhonized with the lamp_service
            return
        self._updatingUI = True
        try:
            if 'color' in new_state:
                self.hue = new_state['color']['h']
                self.saturation = new_state['color']['s']
            if 'brightness' in new_state:
                self.brightness = new_state['brightness']
            if 'on' in new_state:
                self.lamp_is_on = new_state['on']
        finally:
            self._updatingUI = False

        self._updated = True

    def _update_leds(self):
        msg = {'color': {'h': self._hue, 's': self._saturation},
               'brightness': self._brightness,
               'on': self.lamp_is_on,
               'client': MQTT_CLIENT_ID}
        self.mqtt.publish(TOPIC_SET_LAMP_CONFIG,
                          json.dumps(msg).encode('utf-8'),
                          qos=1)
        self._publish_clock = None

    def set_up_GPIO_and_device_status_popup(self):
        self.pi = pigpio.pi()
        self.pi.set_mode(17, pigpio.INPUT)
        self.pi.set_pull_up_down(17, pigpio.PUD_UP)
        self.pi.set_mode(22, pigpio.INPUT)
        self.pi.set_pull_up_down(22, pigpio.PUD_UP)
        Clock.schedule_interval(self._poll_GPIO, 0.05)
        self.network_status_popup = self._build_network_status_popup()
        self.network_status_popup.bind(on_open=self.update_device_status_popup)

    def _build_network_status_popup(self):
        return Popup(title='Device Status',
                     content=Label(text='IP ADDRESS WILL GO HERE'),
                     size_hint=(1, 1), auto_dismiss=False)

    def update_device_status_popup(self, instance):
        interface = "wlan0"
        ipaddr = lampi.lampi_util.get_ip_address(interface)
        deviceid = lampi.lampi_util.get_device_id()
        msg = ("Version: {}\n"
               "{}: {}\n"
               "DeviceID: {}\n"
               "Broker Bridged: {}\n"
               "Async Analytics"
               ).format(
            "",  # version goes here
            interface,
            ipaddr,
            deviceid,
            self.mqtt_broker_bridged)
        instance.content.text = msg

    def on_gpio17_pressed(self, instance, value):
        if value:
            self.network_status_popup.open()
        else:
            self.network_status_popup.dismiss()

    def on_gpio22_pressed(self, instance, value):
        if sm.current == 'lamp' and value:
            self.game_on = True
        elif value:
            self.game_on = False
            self.prev_game_screen = sm.current

        if self.game_on:
            sm.current = self.prev_game_screen
        else:
            sm.current = 'lamp'

    def _poll_GPIO(self, dt):
        # GPIO17 is the rightmost button when looking front of LAMPI
        self.gpio17_pressed = not self.pi.read(17)
        # for tictactoe game
        self.gpio22_pressed = not self.pi.read(22)
