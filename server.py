from utils import ClientServer, GAME_START_TIME, STEP_SPEED, DO_TIMES, ui_manager, assets
from json import loads, dumps
from time import time
import socketserver
import numpy as np
import threading
import signal
import sys
import pygame
SERVER_ADDRESS = ("localhost", 2527)

class GameServer:
    def __init__(self):
        self.lock = threading.Lock()
        self.clients = {}
        self.steps = []
        self.start_time = time()
        self.correct_key = np.random.randint(0, 8)
        self.alive = True
        self.success = False
        self.max_clients = 8

    def generate_client_id(self):
        with self.lock:
            return max(self.clients.keys(), default=-1) + 1

    def generate_steps(self):
        with self.lock:
            self.steps = ClientServer.generate_steps()

    def update_game_status(self, client_id, data): # move UI to utils?
        with self.lock:
            if data.get("quit"):
                self.alive = False
            if data.get("clicked"):
                pygame.init()
                screen_result = pygame.display.set_mode((300, 200))
                pygame.display.set_caption("Limbo!")
                pygame.display.set_icon(assets.assets['logo'])
                self.success = self.correct_key == client_id

                win_lose_bg = pygame.transform.scale(assets.assets['resultBG'], (300, 200))

                if self.success:
                    title = "Congratulations!"
                    text = "You did it :)"
                    title_color = (0,171,102)
                    text_color = (46,139,87)
                else:
                    title = "Not even close"
                    text = "Give it another try"
                    title_color = (220,20,60)
                    text_color = (240, 128, 128)

                title_surface = ui_manager.render_text(title, color=title_color, use_shadow=True, font_size=32)
                text_surface = ui_manager.render_text(text, color=text_color, use_shadow=True, font_size=26)

                CLOSE_EVENT = pygame.USEREVENT + 1
                pygame.time.set_timer(CLOSE_EVENT, 5000)

                running_result = True
                while running_result:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running_result = False
                        elif event.type == CLOSE_EVENT:
                            running_result = False

                    if running_result:
                        screen_result.blit(win_lose_bg, (0, 0))
                        screen_result.blit(title_surface, (150 - title_surface.get_width() / 2, 50))
                        screen_result.blit(text_surface, (150 - text_surface.get_width() / 2, 150))
                        pygame.display.flip()

                self.alive = False
                pygame.quit()
                sys.exit()

    def get_reply(self, client_id):
        current_time = time() - self.start_time
        if not self.alive:
            return {"close": True}
        else:
            return {
                "id": client_id,
                "position": ClientServer.get_pos(client_id, current_time, self.steps),
                "alive": self.alive,
                "highlight": 1 if client_id == self.correct_key and 2 < current_time < 3 else -1,
                "success": self.success,
                "clickable": current_time > GAME_START_TIME + STEP_SPEED * DO_TIMES + 0.5,
            }

class ServerHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.client_id = game_server.generate_client_id()
        if self.client_id >= game_server.max_clients or not game_server.alive:
            self.request.close()
            return
        game_server.clients[self.client_id] = self.request
        if len(game_server.clients) == 1:
            game_server.generate_steps()
            game_server.start_time = time()

    def handle(self):
        try:
            while game_server.alive:
                data = loads(self.request.recv(1024).decode('utf-8'))
                game_server.update_game_status(self.client_id, data)
                self.send_reply()
        except OSError:
            pass

    def send_reply(self):
        reply = game_server.get_reply(self.client_id)
        self.request.sendall(dumps(reply).encode('utf-8') + b'\n')

    def finish(self):
        with game_server.lock:
            game_server.clients.pop(self.client_id, None)
            if not game_server.clients:
                game_server.alive = False

def signal_handler(sig, frame):
    try:
        if server:
            server.shutdown()
            server.server_close()
    except Exception as e:
        print(f"Error shutting down server: {e}")
    finally:
        sys.exit(0)

if __name__ == '__main__':
    server = None
    try:
        game_server = GameServer()
        server = socketserver.ThreadingTCPServer(SERVER_ADDRESS, ServerHandler)
        server.allow_reuse_address = True
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        server.serve_forever()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if server:
            server.shutdown()
            server.server_close()