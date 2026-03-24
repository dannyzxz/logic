import pygame as py

py.init()

AUTOSAVE = py.USEREVENT + 1
CHANGE_STATE = py.USEREVENT + 2
MESSAGE = py.USEREVENT + 3
PLAY_SFX = py.USEREVENT + 4
MUSIC_END_EVENT = py.USEREVENT + 5
SET_ACTIVE_BLOCK = py.USEREVENT + 6
SET_PENDING_PORT = py.USEREVENT + 7

py.time.set_timer(AUTOSAVE, 1000 * 120)
py.mixer.music.set_endevent(MUSIC_END_EVENT)

def set_state(state):
    custom_event = py.event.Event(CHANGE_STATE, state=state)
    py.event.post(custom_event)

def queue_message(message):
    custom_event = py.event.Event(MESSAGE, message=message)
    py.event.post(custom_event)

def play_sound(name):
    custom_event = py.event.Event(PLAY_SFX, name=name)
    py.event.post(custom_event)

def set_active_block(block):
    custom_event = py.event.Event(SET_ACTIVE_BLOCK, block=block)
    py.event.post(custom_event)

def set_pending_port(port):
    custom_event = py.event.Event(SET_PENDING_PORT, port=port)
    py.event.post(custom_event)
