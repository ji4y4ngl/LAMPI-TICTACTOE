import platform
from kivy.app import App
from kivy.properties import NumericProperty, AliasProperty, BooleanProperty
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from math import fabs
import json
from paho.mqtt.client import Client
import pigpio
from lamp_common import *
import lampi.lampi_util
# from mixpanel import Mixpanel
# from mixpanel_async import AsyncBufferedConsumer

from kivy.lang import Builder
# from lampi.toe import ToeScreen
from kivy.uix.screenmanager import ScreenManager, Screen

MQTT_CLIENT_ID = "lamp_ui"
sm = ScreenManager()

class MainScreen(Screen):
    pass

# --------------------------------------------------------------------

class ToeScreen(Screen):
    # Define Who's turn it is
	turn = "X"

	# Keep Track of win or lose
	winner = False
	
	# Keep track of winners and losers
	X_win = 0
	O_win = 0

	# No Winner
	def no_winner(self):
		if self.winner == False and \
		self.root.ids.btn1.disabled == True and \
		self.root.ids.btn2.disabled == True and \
		self.root.ids.btn3.disabled == True and \
		self.root.ids.btn4.disabled == True and \
		self.root.ids.btn5.disabled == True and \
		self.root.ids.btn6.disabled == True and \
		self.root.ids.btn7.disabled == True and \
		self.root.ids.btn8.disabled == True and \
		self.root.ids.btn9.disabled == True:
			self.root.ids.score.text = "IT'S A TIE!!"

	# End The Game
	def end_game(self, a,b,c):
		self.winner = True
		a.color = "red"
		b.color = "red"
		c.color = "red"

		# Disable the buttons
		self.disable_all_buttons()

		# Set Label for winner
		self.root.ids.score.text = f"{a.text} Wins!"

		# Keep track of winners and loser
		if a.text == "X":
			self.X_win = self.X_win + 1	
		else:
			self.O_win = self.O_win + 1

		self.root.ids.game.text = f"X Wins: {self.X_win}  |  O Wins: {self.O_win}"

	def disable_all_buttons(self):
		# Disable The Buttons
		self.root.ids.btn1.disabled = True
		self.root.ids.btn2.disabled = True
		self.root.ids.btn3.disabled = True
		self.root.ids.btn4.disabled = True
		self.root.ids.btn5.disabled = True
		self.root.ids.btn6.disabled = True
		self.root.ids.btn7.disabled = True
		self.root.ids.btn8.disabled = True
		self.root.ids.btn9.disabled = True

	def win(self):
		# Across
		if self.root.ids.btn1.text != "" and self.root.ids.btn1.text == self.root.ids.btn2.text and self.root.ids.btn2.text == self.root.ids.btn3.text:
			self.end_game(self.root.ids.btn1, self.root.ids.btn2, self.root.ids.btn3)

		if self.root.ids.btn4.text != "" and self.root.ids.btn4.text == self.root.ids.btn5.text and self.root.ids.btn5.text == self.root.ids.btn6.text:
			self.end_game(self.root.ids.btn4, self.root.ids.btn5, self.root.ids.btn6)

		if self.root.ids.btn7.text != "" and self.root.ids.btn7.text == self.root.ids.btn8.text and self.root.ids.btn8.text == self.root.ids.btn9.text:
			self.end_game(self.root.ids.btn7, self.root.ids.btn8, self.root.ids.btn9)
		# Down
		if self.root.ids.btn1.text != "" and self.root.ids.btn1.text == self.root.ids.btn4.text and self.root.ids.btn4.text == self.root.ids.btn7.text:
			self.end_game(self.root.ids.btn1, self.root.ids.btn4, self.root.ids.btn7)

		if self.root.ids.btn2.text != "" and self.root.ids.btn2.text == self.root.ids.btn5.text and self.root.ids.btn5.text == self.root.ids.btn8.text:
			self.end_game(self.root.ids.btn2, self.root.ids.btn5, self.root.ids.btn8)

		if self.root.ids.btn3.text != "" and self.root.ids.btn3.text == self.root.ids.btn6.text and self.root.ids.btn6.text == self.root.ids.btn9.text:
			self.end_game(self.root.ids.btn3, self.root.ids.btn6, self.root.ids.btn9)

		# Diagonal 
		if self.root.ids.btn1.text != "" and self.root.ids.btn1.text == self.root.ids.btn5.text and self.root.ids.btn5.text == self.root.ids.btn9.text:
			self.end_game(self.root.ids.btn1, self.root.ids.btn5, self.root.ids.btn9)

		if self.root.ids.btn3.text != "" and self.root.ids.btn3.text == self.root.ids.btn5.text and self.root.ids.btn5.text == self.root.ids.btn7.text:
			self.end_game(self.root.ids.btn3, self.root.ids.btn5, self.root.ids.btn7)

		self.no_winner()

	def presser(self, btn):
		if self.turn == 'X':
			btn.text = "X"
			btn.disabled = True
			self.root.ids.score.text = "O's Turn!"
			self.turn = "O"
		else:
			btn.text = "O"
			btn.disabled = True
			self.root.ids.score.text = "X's Turn!"
			self.turn = "X"

		# Check To See if won
		self.win()

	def restart(self):
		# Reset Who's Turn It Is
		self.turn = "X"

		# Enable The Buttons
		self.root.ids.btn1.disabled = False
		self.root.ids.btn2.disabled = False
		self.root.ids.btn3.disabled = False
		self.root.ids.btn4.disabled = False
		self.root.ids.btn5.disabled = False
		self.root.ids.btn6.disabled = False
		self.root.ids.btn7.disabled = False
		self.root.ids.btn8.disabled = False
		self.root.ids.btn9.disabled = False

		# Clear The Buttons
		self.root.ids.btn1.text = ""
		self.root.ids.btn2.text = ""
		self.root.ids.btn3.text = ""
		self.root.ids.btn4.text = ""
		self.root.ids.btn5.text = ""
		self.root.ids.btn6.text = ""
		self.root.ids.btn7.text = ""
		self.root.ids.btn8.text = ""
		self.root.ids.btn9.text = ""

		# Reset The Button Colors
		self.root.ids.btn1.color = "green"
		self.root.ids.btn2.color = "green"
		self.root.ids.btn3.color = "green"
		self.root.ids.btn4.color = "green"
		self.root.ids.btn5.color = "green"
		self.root.ids.btn6.color = "green"
		self.root.ids.btn7.color = "green"
		self.root.ids.btn8.color = "green"
		self.root.ids.btn9.color = "green"

		# Reset The Score Label
		self.root.ids.score.text = "X GOES FIRST!"

		# Reset The Winner Variable
		self.winner = False

# -----------------------------------------------------------------------------

class LampiApp(App):

    def build(self):
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(ToeScreen(name='toe'))
		# ToeScreen.theme_cls.theme_style = "Dark"
		# ToeScreen.theme_cls.primary_palette = "BlueGray"
        # Builder.load_file('toe.kv')
        # Builder.load_file('main.kv')
        sm.current = 'main'

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
    game_on = False

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
        self._track_ui_event('Slider Change',
                             {'slider': 'hue-slider', 'value': value})
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_saturation(self, instance, value):
        if self._updatingUI:
            return
        # self._track_ui_event('Slider Change',
        #                      {'slider': 'saturation-slider', 'value': value})
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_brightness(self, instance, value):
        if self._updatingUI:
            return
        # self._track_ui_event('Slider Change',
        #                      {'slider': 'brightness-slider', 'value': value})
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_lamp_is_on(self, instance, value):
        if self._updatingUI:
            return
        # self._track_ui_event('Toggle Power', {'isOn': value})
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
        if sm.current == 'main' and value:
            self.game_on = True
        if sm.current == 'toe' and value:
            self.game_on = False

        if self.game_on:
            sm.current = 'toe'
        else:
            sm.current = 'main'

    def _poll_GPIO(self, dt):
        # GPIO17 is the rightmost button when looking front of LAMPI
        self.gpio17_pressed = not self.pi.read(17)
        # for tictactoe game
        self.gpio22_pressed = not self.pi.read(22)
