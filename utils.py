from random import choice
from pathlib import Path
from time import sleep
import numpy as np
import subprocess
import threading
import platform
import pygame
import json
import sys
import os

if platform.system() in ['Windows', 'Darwin']: import pygetwindow as gw
else: gw = None # Not compatible with Linux

# SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080     Maybe refactor for compatibility with different screen types *-*     Update: pygame.display.Info() fixed this??
WINDOW_WIDTH, WINDOW_HEIGHT = 150, 150
SPACING = 100
DO_TIMES = 30
GAME_START_TIME = 5.4
STEP_SPEED = 0.3    # 60FPS / 200

class StepMap:
    MAP = {
    0:  {0: 4, 1: 5, 2: 6, 3: 7, 4: 0, 5: 1, 6: 2, 7: 3},
    1:  {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 0},
    2:  {0: 7, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6},
    3:  {0: 5, 1: 4, 4: 1, 5: 0, 2: 7, 3: 6, 6: 3, 7: 2},
    4:  {0: 3, 1: 2, 2: 1, 3: 0, 4: 7, 5: 6, 6: 5, 7: 4},
    5:  {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1, 7: 0},
    6:  {0: 1, 1: 5, 5: 4, 4: 0, 2: 3, 3: 7, 7: 6, 6: 2},
    7:  {1: 0, 5: 1, 4: 5, 0: 4, 3: 2, 7: 3, 6: 7, 2: 6},
    8:  {1: 0, 5: 1, 4: 5, 0: 4, 2: 3, 3: 7, 7: 6, 6: 2},
    9:  {0: 6, 1: 7, 2: 4, 3: 5, 4: 2, 5: 3, 6: 0, 7: 1},
    10: {0: 5, 1: 6, 2: 7, 3: 3, 4: 4, 5: 0, 6: 1, 7: 2},
    11: {0: 0, 1: 4, 2: 5, 3: 6, 4: 1, 5: 2, 6: 3, 7: 7},
}

    FORBIDDEN_PAIRS = {(10, 9), (11, 9), (9, 10), (9, 11), (1, 2), (2, 1)}
    
class ConfigManager:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            print(f"Configuration file {self.config_path} not found. Using defaults.")
            return self.default_config()
        except json.JSONDecodeError:
            print(f"Error decoding {self.config_path}. Using defaults.")
            return self.default_config()

    def default_config(self):
        return {
            "audio": {"musicEnabled": True, "sfxEnabled": True, "sfxVolume": 0.5, "musicVolume": 0.5},
            "preferences": {"borderless": False, "transparent": False, "doNotOption": False},
            "assets": {}
        }

    def save_config(self):
        try:
            with open(self.config_path, 'w') as config_file:
                json.dump(self.config, config_file, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def toggle_preference(self, preference_key): # tbh idk what I did here :3
        recognized_keys = ["borderless", "musicEnabled", "sfxEnabled", "doNotOption", "transparent"]

        if preference_key in recognized_keys:
            if preference_key == "borderless":
                self.config["preferences"]["borderless"] = not self.config["preferences"].get("borderless", False)
                flags = pygame.NOFRAME if self.config["preferences"]["borderless"] else 0
                pygame.display.set_mode((750, 600), flags)
            elif preference_key == "musicEnabled":
                self.config["audio"]["musicEnabled"] = not self.config["audio"].get("musicEnabled", True)
                if self.config["audio"]["musicEnabled"]: # if it works dont touch it...
                    pygame.mixer.music.set_volume(self.config["audio"]["musicVolume"])
                    try:
                        pygame.mixer.music.play(-1)
                    except:
                        assets.assets["bgMusic"].play(-1)
                else:
                    try:
                        pygame.mixer.music.stop()
                        assets.assets["bgMusic"].stop()
                    except:
                        assets.assets["bgMusic"].stop()
            elif preference_key == "sfxEnabled":
                self.config["audio"]["sfxEnabled"] = not self.config["audio"].get("sfxEnabled", True)
            elif preference_key == "doNotOption":
                self.config["preferences"]["doNotOption"] = not self.config["preferences"].get("doNotOption", False)
            elif preference_key == "transparent":
                self.config["preferences"]["transparent"] = not self.config["preferences"].get("transparent", False)
            self.save_config()
            return preference_key
        else:
            print(f"Preference key '{preference_key}' not recognized")
            return None

class AssetManager: # refactor this?
    SUPPORTED_EXTENSIONS = {
        'audio': ['.mp3', '.wav', '.ogg'],
        'image': ['.png', '.jpg', '.jpeg', '.ico'],
        'font': ['.otf', '.ttf']
    }

    def __init__(self, assets_path, config):
        self.assets_path = assets_path
        self.assets = self.load_assets(config.get("assets", {}))

    def load_assets(self, asset_paths):
        assets = {}
        for asset_name, path_str in asset_paths.items():
            path = self.assets_path / path_str
            try:
                asset_type = self.get_asset_type(path.suffix)
                if asset_type == 'audio':
                    assets[asset_name] = pygame.mixer.Sound(str(path))
                elif asset_type == 'image':
                    assets[asset_name] = pygame.image.load(str(path))
                elif asset_type == 'font':
                    assets[asset_name] = pygame.font.Font(str(path), 42)
                else:
                    print(f"Unsupported file type for {asset_name}: {path.suffix}")
            except:
                sys.exit(0)
        return assets

    def get_asset_type(self, file_extension):
        for asset_type, extensions in self.SUPPORTED_EXTENSIONS.items():
            if file_extension.lower() in extensions:
                return asset_type
        return None

class UIManager:
    def __init__(self, assets, config, base_dir):
        self.assets = assets
        self.config = config
        self.base_dir = base_dir

    def render_text(self, text, color=(255, 255, 255), shadow_color=(0, 0, 0), use_shadow=True, font_size=42):
        font_file_name = self.config["assets"].get('font', 'pusab.otf')
        font_path = self.base_dir / "assets" / font_file_name
        font = pygame.font.Font(str(font_path), font_size)
        text_surface = font.render(text, True, color)
        
        if use_shadow:
            shadow_offset = 3
            shadow_surface = font.render(text, True, shadow_color)
            combined_surface = pygame.Surface((text_surface.get_width() + shadow_offset, text_surface.get_height() + shadow_offset), pygame.SRCALPHA)
            combined_surface.blit(shadow_surface, (shadow_offset, shadow_offset))
            combined_surface.blit(text_surface, (0, 0))
            return combined_surface
        else:
            return text_surface

    def draw_checkbox(self, screen, position, is_checked):
        selected_image_key = 'uncheckedBox' if is_checked else 'checkedBox'
        
        checkbox_image = pygame.transform.scale(self.assets[selected_image_key], (50, 50))
        screen.blit(checkbox_image, position)

    def play_sound(self, sound_key):
        if self.config.get("audio", {}).get("sfxEnabled", True):
            try:
                self.assets[sound_key].play()
            except KeyError:
                print(f"Sound key '{sound_key}' not found in assets.")
                
class AnimationManager:
    @staticmethod
    def ease_in_out_quad(t):
        if t < 0.5: return 2 * t * t
        else: return -2 * t * t + 4 * t - 1

    @staticmethod
    def fade_in(screen, final_surface, duration=200):
        fade_surface = final_surface.copy()
        start_time = pygame.time.get_ticks()
        clock = pygame.time.Clock()

        while True:
            elapsed = pygame.time.get_ticks() - start_time
            if elapsed > duration: break
            alpha = min(255, int(255 * AnimationManager.ease_in_out_quad(elapsed / duration)))
            fade_surface.set_alpha(alpha)
            screen.blit(fade_surface, (0, 0))
            pygame.display.update()
            clock.tick(60)

        fade_surface.set_alpha(255)
        screen.blit(fade_surface, (0, 0))
        pygame.display.update()

    @staticmethod
    def animate_scale(original_rect, hover_start_time, is_hovered, current_time, duration=200):
        if hover_start_time is None:
            return original_rect

        elapsed = current_time - hover_start_time

        if elapsed > duration:
            if is_hovered:
                target_scale = 1.1
            else:
                return original_rect
        else:
            if is_hovered:
                progress = elapsed / duration
                target_scale = 1 + (0.1 * progress)
            else:
                progress = 1 - (elapsed / duration)
                target_scale = 1 + (0.1 * progress)

        original_size = original_rect.size
        current_size = (int(original_size[0] * target_scale), int(original_size[1] * target_scale))
        
        current_rect = original_rect.copy()
        current_rect.size = current_size
        current_rect.center = original_rect.center
        
        return current_rect
    
    @staticmethod
    def update_hover_animation(key, is_hovered, current_time, hover_animations):
        if key not in hover_animations or hover_animations[key]['is_hovered'] != is_hovered:
            hover_animations[key] = {'start_time': current_time, 'is_hovered': is_hovered}
            
class Slider: # Maybe add a hover effect and background for the filled part
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, volume_type='sfx'):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.volume_type = volume_type
        
        self.bg_img = pygame.transform.scale(assets.assets['sliderBG'], (w, h))
        self.selector_img = assets.assets['sliderThumb']
        
        selector_width = self.selector_img.get_width()
        selector_height = self.selector_img.get_height()
        self.slider_rect = pygame.Rect(x, y + (h - selector_height) // 2, selector_width, selector_height)
        
        self.dragging = False
        self.update_slider_position()

    def draw(self, screen):
        screen.blit(self.bg_img, self.rect.topleft)
        screen.blit(self.selector_img, (self.slider_rect.x, self.slider_rect.y))

    def update_slider_position(self):
        position = (self.val - self.min_val) / (self.max_val - self.min_val) * (self.rect.width - self.slider_rect.width)
        self.slider_rect.x = self.rect.x + position

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and self.slider_rect.collidepoint(mouse_pos):
            self.dragging = True
            self.drag_offset = mouse_pos[0] - self.slider_rect.x
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouseX = event.pos[0] - self.drag_offset
            newPosition = min(max(mouseX, self.rect.x), self.rect.x + self.rect.width - self.slider_rect.width)
            self.val = (newPosition - self.rect.x) / (self.rect.width - self.slider_rect.width) * (self.max_val - self.min_val) + self.min_val
            self.update_slider_position()
            self.apply_volume_setting()

    def apply_volume_setting(self):
        self.val = round(self.val, 2)
        if self.volume_type == 'sfx':
            for sound_key, sound in assets.assets.items():
                if isinstance(sound, pygame.mixer.Sound):
                    sound.set_volume(self.val)
            config.config["audio"]["sfxVolume"] = self.val
        elif self.volume_type == 'music':
            pygame.mixer.music.set_volume(self.val)
            config.config["audio"]["musicVolume"] = self.val
        config.save_config()

class ClientServer:
    def __init__(self):
        self.python_cmd = "python" if "WindowsApps" in os.environ['PATH'] else "python3"
        self.base_dir = Path(__file__).resolve().parent

    def start_game_instances(self):
        server_script_path = str(self.base_dir / "server.py")
        client_script_path = str(self.base_dir / "client.py")

        server_process = subprocess.Popen([self.python_cmd, server_script_path])
        
        threads = []
        for _ in range(8):
            thread = threading.Thread(target=lambda: subprocess.run([self.python_cmd, client_script_path]))
            thread.start()
            threads.append(thread)
            sleep(0.2)
        
        for thread in threads:
            thread.join()
        
        server_process.terminate()
    
    @staticmethod
    def minimize_all_windows(): # future feature?
        if gw is not None:
            for window in gw.getAllWindows():
                window.minimize()
                
    # Window transparency bugged gotta sort out this sometime, not sure when tho *o*    Update: nvm kinda fixed but not compatible with linux
    # https://stackoverflow.com/questions/4549213/make-a-window-transparent-using-win32/4550243#4550243
    # https://stackoverflow.com/questions/23585212/transparent-hwnd-window
    # Transparent window only possible on Windows, maybe fake transparency on linux with a snapshot of the desktop
    @staticmethod
    def set_window_transparency(hwnd, color_key=(0, 0, 0)):
        from ctypes import windll
        import win32gui, win32con, win32api

        exstyle = windll.user32.GetWindowLongW(hwnd, win32con.GWL_EXSTYLE)
        windll.user32.SetWindowLongW(hwnd, win32con.GWL_EXSTYLE, exstyle | win32con.WS_EX_LAYERED)

        win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*color_key), 0, win32con.LWA_COLORKEY)
        
    @staticmethod
    def lerp(p1, p2, amt):
        return (1 - amt) * np.array(p1) + amt * np.array(p2)

    @staticmethod
    def serp(p1, p2, amt):
        return ClientServer.lerp(p1, p2, (1 - np.cos(amt * np.pi)) / 2)

    @staticmethod
    def get_static_pos(client_id):
        x = SCREEN_WIDTH // 2 - WINDOW_WIDTH * 2 - SPACING * 2 + (client_id % 4) * (WINDOW_WIDTH + SPACING)
        y = SCREEN_HEIGHT // 2 - WINDOW_HEIGHT - SPACING + (client_id // 4) * (WINDOW_HEIGHT + SPACING * 2)
        return [x, y]

    @staticmethod
    def get_ellipse_pos(client_id, time_offset):
        x = SCREEN_WIDTH // 2 + np.cos(np.pi * client_id / 4 + time_offset) * SCREEN_WIDTH // 4 - WINDOW_WIDTH // 2
        y = SCREEN_HEIGHT // 2 + np.sin(np.pi * client_id / 4 + time_offset) * SCREEN_HEIGHT // 3 - WINDOW_HEIGHT // 2
        return [int(x), int(y)]

    @staticmethod
    def get_pos(client_id, current_time, steps):
        if current_time < GAME_START_TIME:
            return ClientServer.get_static_pos(client_id)

        running_time = current_time - GAME_START_TIME
        spoofed_id = client_id
        for step in steps[:int(running_time / STEP_SPEED)]:
            spoofed_id = StepMap.MAP[step].get(spoofed_id, spoofed_id)

        if running_time / STEP_SPEED >= len(steps):
            lerped = np.clip((current_time - GAME_START_TIME - STEP_SPEED * DO_TIMES) / 2, 0.0, 1.0)
            lerped = 1 + (lerped - 1) ** 3
            return ClientServer.lerp(ClientServer.get_static_pos(spoofed_id), ClientServer.get_ellipse_pos(client_id, current_time), lerped).tolist()
        
        current_step = steps[int(running_time / STEP_SPEED) % len(steps)]
        return ClientServer.serp(ClientServer.get_static_pos(spoofed_id), ClientServer.get_static_pos(StepMap.MAP[current_step][spoofed_id]), (running_time / STEP_SPEED) % 1).tolist()
    
    @staticmethod
    def generate_steps():
        steps = []
        prev_move = -1
        while len(steps) < DO_TIMES:
            move = choice([m for m in range(12) if m != prev_move and (prev_move, m) not in StepMap.FORBIDDEN_PAIRS])
            steps.append(move)
            prev_move = move
        return steps
    
pygame.init()
pygame.mixer.init()

display_info = pygame.display.Info()

SCREEN_WIDTH, SCREEN_HEIGHT = display_info.current_w, display_info.current_h
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
ASSETS_PATH = BASE_DIR / "assets"

config = ConfigManager(CONFIG_PATH)
assets = AssetManager(ASSETS_PATH, config.config)
ui_manager = UIManager(assets.assets, config.config, BASE_DIR)
animation_manager = AnimationManager()
audio = config.config.get("audio", {})
preferences = config.config.get("preferences", {})
