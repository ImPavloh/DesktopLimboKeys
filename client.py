import os
import sys
import socket
import threading
from time import sleep
from json import loads, dumps

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame
from pygame._sdl2 import Window

from utils import assets, preferences, config, ClientServer

SERVER_ADDRESS = ('localhost', 2527)

class Client:
    def __init__(self, server_address, music_setting, sfx_setting):
        self.id = -1
        self.position = [0, -300]
        self.highlight_amount = 0
        self.alive = True
        self.wants_to_quit = False
        self.clicked = False
        self.clickable = False
        self.success = False
        self.game_over = False
        self.sfx = sfx_setting
        self.music = music_setting
        self.server_address = server_address
        self.id_surface = pygame.Surface((0, 0))
        threading.Thread(target=self.listening_thread).start()
        
    def listening_thread(self):
        buffer = ""
        assigned_client_id = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(self.server_address)
            s.sendall(dumps({"quit": False, "clicked": False}).encode('ascii') + b'\n')
            while not self.game_over:
                sleep(0.02)
                response = s.recv(1024).decode('ascii')
                if not response:
                    break

                buffer += response
                while '\n' in buffer:
                    raw_message, buffer = buffer.split('\n', 1)
                    msg = loads(raw_message)
                    
                    if msg.get("close"):
                        self.game_over = True
                        self.alive = False
                        break

                    self.id, self.position, self.alive, self.success, self.clickable, self.highlight_amount = (
                        msg["id"], msg["position"], msg["alive"], msg["success"],
                        msg["clickable"], min(1, max(self.highlight_amount + msg.get("highlight", 0) * 4 / 60, 0))
                    )
                    if not assigned_client_id and self.id == 0 and self.music:
                        assets.assets['music'].set_volume(config.config['audio']['musicVolume'])
                        assets.assets['music'].play()
                        assigned_client_id = True

                s.sendall(dumps({"quit": self.wants_to_quit, "clicked": self.clicked}).encode('ascii') + b'\n')
                if self.wants_to_quit or not self.alive or self.clicked:
                    self.game_over = True

    def game_loop():
        global client
        
        client = Client(SERVER_ADDRESS, config.config["audio"]["musicEnabled"], config.config["audio"]["sfxEnabled"])
        pgwindow = Window.from_display_module()

        if preferences.get('transparent', False):
            hwnd = pygame.display.get_wm_info()['window']
            ClientServer.set_window_transparency(hwnd, (33, 33, 33))

        running = True
        while running and client.alive:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    client.wants_to_quit = True
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and client.clickable:
                    client.wants_to_quit = True
                    client.clicked = True
                if client.game_over:
                    running = False

            screen.fill((33, 33, 33))
            
            if preferences['doNotOption']:
                dno0 = assets.assets['blueFace']
                dno1 = assets.assets['greenFace']
            else:
                dno0 = assets.assets['redKey']
                dno1 = assets.assets['greenKey']
                
            image_rect = dno0.get_rect(center=(150 / 2, 150 / 2))
            if client.highlight_amount != 0:
                screen.blit(dno1, image_rect)
                dno0.set_alpha(255 - int(client.highlight_amount * 255))
                screen.blit(dno0, image_rect)
            else:
                screen.blit(dno0, image_rect)

            if isinstance(client.position[0], list):
                pgwindow.position = [int(pos) for pos in client.position[0]]
            else:
                pgwindow.position = [int(pos) for pos in client.position]

            pygame.display.flip()
            clock.tick(60)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Limbo!")
    pygame.display.set_icon(assets.assets['logo'])
    
    clock = pygame.time.Clock()
    flags = pygame.NOFRAME if preferences["borderless"] else 0
    screen = pygame.display.set_mode((150, 150), flags=flags | pygame.SRCALPHA)

    Client.game_loop()