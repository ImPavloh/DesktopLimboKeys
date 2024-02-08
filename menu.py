import os
import sys
import platform
import webbrowser
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"  #   \*-*/
import pygame
from utils import config, assets, preferences, ui_manager, animation_manager, Slider, ClientServer, CONFIG_PATH, BASE_DIR

def initialize_game():    
    for sound_key, sound in assets.assets.items():
        if isinstance(sound, pygame.mixer.Sound):
            sound.set_volume(config.config["audio"]["sfxVolume"])

    pygame.mixer.music.load(str(BASE_DIR / "assets" / config.config["assets"]["bgMusic"]))
    pygame.mixer.music.set_volume(config.config["audio"]["musicVolume"])
    pygame.mixer.music.play(-1) if config.config["audio"]["musicEnabled"] else None
        
    flags = pygame.NOFRAME if borderless else 0
    screen = pygame.display.set_mode((750, 600), flags)
    pygame.display.set_caption("Limbo!")
    pygame.display.set_icon(pygame.image.load(str(BASE_DIR / "assets" / config.config["assets"]["logo"])))
    return screen

#  tbh I might reduce the code by simplifying everything but uh nuh (yet)
def open_info(screen):
    global hover_animations
    
    if 'hover_animations' not in globals():
        hover_animations = {}

    info_surface = pygame.Surface((750, 600))
    info_bg = pygame.transform.scale(assets.assets['infoBG'], (750, 600))
    info_surface.blit(info_bg, (0, 0))

    back_button_image = pygame.transform.scale(assets.assets['backLogo'], (75, 75))
    back_button_rect_original = back_button_image.get_rect(topleft=(20, 20))

    pavloh_text = ui_manager.render_text("Pavloh - Creator", color=(255, 255, 0), use_shadow=True)
    pavloh_text_rect = pavloh_text.get_rect(topleft=(110, 125))
    
    back_button_rect = back_button_rect_original.copy()

    info_running = True

    while info_running:
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()

        screen.blit(info_surface, (0, 0))
        info_surface.set_alpha(255)

        is_hovered = back_button_rect.collidepoint(mouse_pos)
        animation_manager.update_hover_animation('back_info', is_hovered, current_time, hover_animations)

        animation_state = hover_animations.get('back_info', {'start_time': current_time, 'is_hovered': False})
        elapsed = current_time - animation_state['start_time']
        target_scale = 1.1 if animation_state['is_hovered'] else 1.0
        back_button_rect = animation_manager.animate_scale(back_button_rect_original, target_scale, animation_state['is_hovered'], elapsed)
        hover_back_button_image = pygame.transform.scale(back_button_image, back_button_rect.size)
        screen.blit(hover_back_button_image, back_button_rect.topleft)

        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_rect.collidepoint(event.pos):
                    ui_manager.play_sound('backSound')
                    return
                elif pavloh_text_rect.collidepoint(event.pos):
                    ui_manager.play_sound('clickSound')
                    webbrowser.open('https://twitter.com/impavloh')
        
        screen.blit(ui_manager.render_text("Credits", color=(255, 255, 255), use_shadow=True), (300, 40))
        
        screen.blit(pavloh_text, pavloh_text_rect.topleft)

        screen.blit(ui_manager.render_text("RobTop - Game Assets", color=(240, 140, 5), use_shadow=True), (110, 200))
        screen.blit(ui_manager.render_text("Mindcap - Lvl Inspiration", color=(200, 140, 50), use_shadow=True), (110, 250))
        screen.blit(ui_manager.render_text("Crohn44 - Keys Inspiration", color=(220, 70, 0), use_shadow=True), (110, 300))
        screen.blit(ui_manager.render_text("Quasar098 - Legacy Code", color=(220, 140, 150), use_shadow=True), (110, 350))
        screen.blit(ui_manager.render_text("Flat-it - Custom Font", color=(160, 140, 140), use_shadow=True), (110, 400))
        screen.blit(ui_manager.render_text("NightHawk22 - Music", color=(140, 140, 246), use_shadow=True), (110, 450))
        
        screen.blit(ui_manager.render_text("Version 1.0", use_shadow=True), (250, 550))
        
        pygame.display.update()
        
def open_settings(screen):
    global preferences, borderless, hover_animations
    
    if 'hover_animations' not in globals():
        hover_animations = {}

    settings_surface = pygame.Surface((750, 600))
    settings_bg = pygame.transform.scale(assets.assets['settingsBG'], (750, 600))
    settings_surface.blit(settings_bg, (0, 0))
    
    back_button_image = pygame.transform.scale(assets.assets['backLogo'], (75, 75))
    back_button_rect_original = back_button_image.get_rect(topleft=(20, 20))
    
    music_rect = pygame.Rect(100, 150, 50, 50)
    sfx_rect = pygame.Rect(100, 225, 50, 50)
    
    music_volume_slider = Slider(333, 155, 273, 40, 0, 1, config.config["audio"].get("musicVolume", 0.5), volume_type='music')
    sfx_volume_slider = Slider(333, 230, 273, 40, 0, 1, config.config["audio"].get("sfxVolume", 0.5), volume_type='sfx')
    
    borderless_rect = pygame.Rect(100, 300, 50, 50)
    transparent_top = 375 if platform != "windows" else 450
    doNotOption_top = 450 if platform != "windows" else 375

    transparent_rect = pygame.Rect(100, transparent_top, 50, 50)
    doNotOption_rect = pygame.Rect(100, doNotOption_top, 50, 50)
    
    settings_running = True
    
    while settings_running:
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        
        screen.blit(settings_surface, (0, 0))
        settings_surface.set_alpha(255)
        
        is_hovered = back_button_rect_original.collidepoint(mouse_pos)
        animation_manager.update_hover_animation('back_settings', is_hovered, current_time, hover_animations)
        
        animation_state = hover_animations.get('back_settings', {'start_time': current_time, 'is_hovered': False})
        elapsed = current_time - animation_state['start_time']
        target_scale = 1.1 if animation_state['is_hovered'] else 1.0
        back_button_rect = animation_manager.animate_scale(back_button_rect_original, target_scale, animation_state['is_hovered'], elapsed)
        hover_back_button_image = pygame.transform.scale(back_button_image, back_button_rect.size)
        screen.blit(hover_back_button_image, back_button_rect.topleft)
           
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_rect.collidepoint(event.pos):
                    ui_manager.play_sound('backSound')
                    return
                elif music_rect.collidepoint(event.pos):
                    ui_manager.play_sound('clickSound')
                    config.toggle_preference("musicEnabled")
                elif sfx_rect.collidepoint(event.pos):
                    ui_manager.play_sound('clickSound')
                    config.toggle_preference("sfxEnabled")
                elif borderless_rect.collidepoint(event.pos):
                    ui_manager.play_sound('clickSound')
                    config.toggle_preference("borderless")
                elif transparent_rect.collidepoint(event.pos):
                    ui_manager.play_sound('clickSound')
                    config.toggle_preference("transparent")
                elif doNotOption_rect.collidepoint(event.pos):
                    ui_manager.play_sound('clickSound')
                    config.toggle_preference("doNotOption")
            if config.config["audio"]["musicEnabled"]:
                music_volume_slider.handle_event(event, pygame.mouse.get_pos())
            if config.config["audio"]["sfxEnabled"]:
                sfx_volume_slider.handle_event(event, pygame.mouse.get_pos())

        ui_manager.draw_checkbox(screen, music_rect, config.config["audio"]["musicEnabled"])
        if config.config["audio"]["musicEnabled"]: music_volume_slider.draw(screen)
        
        ui_manager.draw_checkbox(screen, sfx_rect, config.config["audio"]["sfxEnabled"])
        if config.config["audio"]["sfxEnabled"]: sfx_volume_slider.draw(screen)
        
        ui_manager.draw_checkbox(screen, borderless_rect, preferences["borderless"])
        ui_manager.draw_checkbox(screen, doNotOption_rect, preferences.get("doNotOption", False))

        screen.blit(ui_manager.render_text("Settings", color=(255, 255, 255), use_shadow=True), (300, 40))

        screen.blit(ui_manager.render_text("Music", color=(255, 255, 255), use_shadow=True), (music_rect.right + 20, music_rect.top + 10 ))
        screen.blit(ui_manager.render_text("SFX", color=(255, 255, 255), use_shadow=True), (sfx_rect.right + 20, sfx_rect.top + 10 ))
        screen.blit(ui_manager.render_text("Borderless window", color=(255, 255, 255), use_shadow=True), (borderless_rect.right + 20, borderless_rect.top + 10 ))
        
        if not platform == "windows":
            ui_manager.draw_checkbox(screen, transparent_rect, preferences.get("transparent", False))
            screen.blit(ui_manager.render_text("Transparent background", color=(255, 255, 255), use_shadow=True), (transparent_rect.right + 20, transparent_rect.top + 10))
        
        screen.blit(ui_manager.render_text("Do not...", color=(255, 255, 255), use_shadow=True), (doNotOption_rect.right + 20, doNotOption_rect.top + 10 ))
        
        screen.blit(ui_manager.render_text(f"Settings file located at {CONFIG_PATH.name}", color=(222, 222, 222), use_shadow=True, font_size=24), (150, 575))

        pygame.display.update()

    config.save_config()

def main_menu(screen, images):
    global borderless, hover_animations  
    
    hover_animations = {} if 'hover_animations' not in globals() else hover_animations
    flags = pygame.NOFRAME | pygame.SRCALPHA if borderless else 0
    screen = pygame.display.set_mode((750, 600), flags=flags)

    button_width, button_height = 100, 100
    play_button_width, play_button_height = 150, 150
    info_button_width, info_button_height = 50, 50

    logo_image = pygame.transform.scale(assets.assets['title'], (400, 234))
    settings_button_image = pygame.transform.scale(images['settingsLogo'], (button_width, button_height))
    play_button_image = pygame.transform.scale(images['playLogo'], (play_button_width, play_button_height))
    exit_button_image = pygame.transform.scale(images['exitLogo'], (button_width, button_height))
    info_button_image = pygame.transform.scale(images['infoLogo'], (info_button_width, info_button_height))

    button_spacing = (750 - (2 * button_width + play_button_width)) // 4
    total_width = 2 * button_width + play_button_width + 2 * button_spacing
    start_x = (750 - total_width) // 2

    play_button_x = start_x + button_width + button_spacing
    exit_button_x = play_button_x + play_button_width + button_spacing
    info_button_x = (750 - info_button_width) // 2
    
    small_button_vertical_start = 350
    play_button_vertical_start = small_button_vertical_start + (button_height - play_button_height) // 2
    
    settings_button_rect = settings_button_image.get_rect(topleft=(start_x, small_button_vertical_start))
    play_button_rect = play_button_image.get_rect(topleft=(play_button_x, play_button_vertical_start))
    exit_button_rect = exit_button_image.get_rect(topleft=(exit_button_x, small_button_vertical_start))
    info_button_rect = info_button_image.get_rect(topleft=(info_button_x, small_button_vertical_start + button_height + 75))

    menu_running = True

    logo_rect = logo_image.get_rect(center=(750 // 2, 500 // 3))

    while menu_running:
        screen.blit(images['menuBG'], (0, 0))
        screen.blit(logo_image, logo_rect)
        
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()

        for button_image, button_rect, key in [
            (settings_button_image, settings_button_rect, 'settings'),
            (play_button_image, play_button_rect, 'play'),
            (exit_button_image, exit_button_rect, 'exit'),
            (info_button_image, info_button_rect, 'info')
        ]:
            is_hovered = button_rect.collidepoint(mouse_pos)
            animation_manager.update_hover_animation(key, is_hovered, current_time, hover_animations)
            
            animation_state = hover_animations.get(key, {'start_time': current_time, 'is_hovered': False})
            elapsed = current_time - animation_state['start_time']
            
            target_scale = 1.1 if animation_state['is_hovered'] else 1.0
            hover_button_rect = animation_manager.animate_scale(button_rect, target_scale, animation_state['is_hovered'], elapsed)
            
            hover_button_image = pygame.transform.scale(button_image, hover_button_rect.size)
            screen.blit(hover_button_image, hover_button_rect.topleft)
    
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button_rect.collidepoint(mouse_pos):
                    menu_running = False
                    ui_manager.play_sound('playSound')
                    animation_manager.fade_in(screen, menu_surface, 600)
                    pygame.quit()
                    client_server = ClientServer()
                    client_server.start_game_instances()
                elif settings_button_rect.collidepoint(mouse_pos):
                    ui_manager.play_sound('clickSound')
                    animation_manager.fade_in(screen, menu_surface, 200)
                    open_settings(screen)
                elif info_button_rect.collidepoint(mouse_pos):
                    ui_manager.play_sound('clickSound')
                    animation_manager.fade_in(screen, menu_surface, 200)
                    open_info(screen)
                elif exit_button_rect.collidepoint(mouse_pos):
                    ui_manager.play_sound('backSound')
                    menu_running = False
                    animation_manager.fade_in(screen, menu_surface, 600)
                    pygame.quit()
                    sys.exit()

        try:
            pygame.display.update()
        except:
            print('Thanks for playing!')
            pygame.quit()
            sys.exit()
    
if __name__ == "__main__":
    os.environ['SDL_VIDEO_WINDOW_POS'] = "center"
    borderless = preferences.get("borderless", False)
    
    screen = initialize_game()
    clock = pygame.time.Clock()
    menu_surface = pygame.Surface((750, 600))
    menu_surface.fill((0, 0, 0))
    
    main_menu(screen, assets.assets)