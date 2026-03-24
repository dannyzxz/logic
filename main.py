import pygame as py

from game_managers.game import Game

from setup.colors import GRAY, DARK_GRAY
from setup.events import AUTOSAVE, CHANGE_STATE, MESSAGE, PLAY_SFX, SET_ACTIVE_BLOCK, SET_PENDING_PORT, queue_message, set_active_block

py.mixer.pre_init(44100, -16, 2, 512)
py.init()

# todo: more sfx, fix scene loading (all blocks offset, most offscreen)

# Fix macro evaluation (ex. flip flops are very strange), 


def handle_left_click(game: Game, e):
    game.controller.check_for_block_clicks(e) # set block.moving = True and active_block
    game.controller.check_for_sidebar_item_creation(e) # click test on sidebar items

    game.controller.handle_port_connections(game.pending_port, e.pos) # validate ports + connect 
    game.ui.sidebar.check_resize(e.pos) # check for resize rect colllision

    for block in game.scene.blocks:
        if block.rect.collidepoint(e.pos):
            block.on_click()

def handle_left_button_up(game: Game):
    if game.active_block:
        game.active_block.moving = False
    game.active_block = None
    game.ui.sidebar.stop_resize()

# helpers for playing()

def playing(game: Game, events):
    game.ui.screen.fill(GRAY)
    for e in events:
        if e.type == py.KEYDOWN: 
            if e.key == py.K_ESCAPE:
                game.ui.start_pause_menu()
            
        elif e.type == py.MOUSEBUTTONDOWN: 
            if e.button == 1: # Left click
                handle_left_click(game, e)

            elif e.button == 3:  # Right click
                game.controller.check_right_clicks(e.pos) # check for wire deletion and block lock toggling

        elif e.type == py.MOUSEBUTTONUP: # Reset movement on button up
            if e.button == 1:
                handle_left_button_up(game)

        elif e.type == py.MOUSEWHEEL:
            if game.ui.sidebar.visible and py.mouse.get_pos()[0] < game.ui.sidebar.rect.right:
                game.ui.sidebar.scroll(-e.y)

    game.controller.check_click_hold() 
    # handle moving blocks and dragging wires 
    # which cant be handled by single click checks

    game.update_game()

def paused(game: Game, events):
    for e in events:
        if e.type == py.KEYDOWN:
            if e.key == py.K_ESCAPE:
                game.ui.start_game()
            # Unpause

    game.ui.draw_game(game.pending_port)

def macro_creation(game: Game, events):
    for e in events:
        if e.type == py.KEYDOWN:
            if e.key == py.K_RETURN:    
                game.handle_macro_name_return()
            
            elif e.key == py.K_ESCAPE:
                game.ui.start_confirm_menu("Cancel macro creation?", game.ui.start_pause_menu)
        
                    
    game.ui.draw_game(game.pending_port)

def saving_scene(game: Game, events):
    for e in events:
        if e.type == py.KEYDOWN and e.key == py.K_RETURN:
            if game.ui.textbox.selected:
                game.handle_save_name_return()
            
            else:
                game.ui.start_pause_menu()

def save_load_menu(game: Game, events):
    for e in events:
        if e.type == py.KEYDOWN:
            if e.key == py.K_ESCAPE:
                for btn in game.ui.load_buttons:
                    btn.hide()
                game.ui.start_game()

    game.ui.screen.fill(GRAY)

def macro_load_menu(game: Game, events):
    for e in events:
        if e.type == py.KEYDOWN and e.key == py.K_ESCAPE:
            game.ui.start_pause_menu()

    game.ui.screen.fill(GRAY)

def audio_menu(game: Game, events):
    for e in events:
        if e.type == py.KEYDOWN and e.key == py.K_ESCAPE:
            game.ui.start_pause_menu()

    game.ui.screen.fill(GRAY)
    game.update_sliders(events)

def confirmation(game: Game, events):
    game.ui.screen.fill(GRAY)

def help(game: Game, events):
    for e in events:
        if e.type == py.KEYDOWN and e.key == py.K_ESCAPE:
            game.ui.start_pause_menu()

    game.ui.screen.fill(DARK_GRAY)

STATE_HANDLERS = {
    "game": playing,
    "paused": paused,
    "macro_creation": macro_creation,
    "saving_scene": saving_scene,
    "save_load_menu": save_load_menu,
    "macro_load_menu": macro_load_menu,
    "audio_menu": audio_menu,
    "confirmation": confirmation,
    "help": help,
}

game = Game()

while game.running:
    game.clock.tick(120)
    events = py.event.get()

    for e in events:
        if e.type == py.QUIT:
            game.running = False

        elif e.type == AUTOSAVE:
            game.handle_autosave()

        elif e.type == CHANGE_STATE:
            game.state = e.state

        elif e.type == MESSAGE:
            game.ui.queue_message(e.message)

        elif e.type == PLAY_SFX:
            game.audio.play_sound(e.name)

        elif e.type == SET_ACTIVE_BLOCK:
            game.active_block = e.block

        elif e.type == SET_PENDING_PORT:
            game.pending_port = e.port
        
        game.audio.handle_event(e)

    handler = STATE_HANDLERS.get(game.state)

    if handler:
        handler(game, events)

    else:
        queue_message(f"DEBUG: handler not found for state: {game.state}")

    game.ui.screen.fill(GRAY)
    game.ui.draw(game.state, game.pending_port, events)
    py.display.flip()