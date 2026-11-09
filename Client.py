import sys
import os
import pygame
import requests

# 桌面 client 在本機執行，透過這個網址呼叫雲端 FastAPI server。
# 部署至 Render 後請修改此網址為您的 Render 網址
API_BASE_URL = "https://mon-mid-term.onrender.com"
# 顏色定義
COLOR_BG = (18, 18, 19)
COLOR_TEXT = (255, 255, 255)
COLOR_EMPTY = (58, 58, 60)
COLOR_CORRECT = (83, 141, 78)   # 綠色
COLOR_PRESENT = (181, 159, 59)  # 黃色
COLOR_ABSENT = (58, 58, 60)     # 灰色
COLOR_PANEL_BG = (24, 24, 25)
COLOR_LINE = (50, 50, 50)

pygame.init()
# 任務三：將 Pygame 視窗寬度從 500 擴大為 700
WIDTH, HEIGHT = 700, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Wordle + FastAPI Client")
font = pygame.font.SysFont("Arial", 36, bold=True)
small_font = pygame.font.SysFont("Arial", 18)
sidebar_font = pygame.font.SysFont("Arial", 20, bold=True)

class WordleGame:
    def __init__(self):
        self.game_id = None
        self.grid = [["" for _ in range(5)] for _ in range(6)]
        self.colors = [[COLOR_EMPTY for _ in range(5)] for _ in range(6)]
        self.row = 0
        self.col = 0
        self.game_over = False
        self.message = "Press ENTER to submit, R to restart"
        
        # 任務三與任務四新增變數
        self.hard_mode = False
        self.history = []
        self.stats = {"total_games": 0, "wins": 0, "win_rate": 0}
        
        self.start_new_game()

    def start_new_game(self):
        """ 向 FastAPI 伺服器請求建立新的一局 """
        try:
            # 任務四：發送 hard_mode 參數至後端
            payload = {"hard_mode": self.hard_mode}
            res = requests.post(f"{API_BASE_URL}/api/new-game", json=payload, timeout=60)
            if res.status_code == 200:
                data = res.json()
                self.game_id = data["game_id"]
                self.grid = [["" for _ in range(5)] for _ in range(6)]
                self.colors = [[COLOR_EMPTY for _ in range(5)] for _ in range(6)]
                self.row = 0
                self.col = 0
                self.game_over = False
                self.history = []
                if "stats" in data:
                    self.stats = data["stats"]
                mode_str = "HARD" if self.hard_mode else "Normal"
                self.message = f"New game started! ({mode_str} Mode)"
            else:
                self.message = "Server error starting new game."
        except requests.exceptions.RequestException:
            self.message = "Cannot connect to FastAPI server!"

    def submit_guess(self):
        """ 將當前行單字發送至 FastAPI 驗證 """
        if self.col < 5:
            self.message = "Not enough letters!"
            return

        guess_word = "".join(self.grid[self.row])
        try:
            payload = {"game_id": self.game_id, "guess": guess_word}
            res = requests.post(f"{API_BASE_URL}/api/guess", json=payload, timeout=60)
            
            if res.status_code == 200:
                data = res.json()
                feedback = data["feedback"]
                if "stats" in data:
                    self.stats = data["stats"]
                
                # 依據後端回傳更新格子顏色
                for i in range(5):
                    if feedback[i] == "correct":
                        self.colors[self.row][i] = COLOR_CORRECT
                    elif feedback[i] == "present":
                        self.colors[self.row][i] = COLOR_PRESENT
                    else:
                        self.colors[self.row][i] = COLOR_ABSENT

                # 任務三：記錄歷史單字
                self.history.append(guess_word)

                if data["is_correct"]:
                    self.message = "Congratulations! You won! Press R to restart."
                    self.game_over = True
                else:
                    self.row += 1
                    self.col = 0
                    if self.row == 6:
                        # 任務一：6 次失敗時明確顯示答案 target_word
                        target_word = data.get("target_word", "UNKNOWN")
                        self.message = f"Game Over! The word was {target_word}. Press R to restart."
                        self.game_over = True
                    else:
                        # 任務一：顯示剩餘次數
                        tries_left = 6 - self.row
                        self.message = f"Keep guessing! ({tries_left} tries left)"
            else:
                # 任務二與任務四：錯誤處理與不扣次數
                detail = res.json().get("detail", "Error processing guess")
                if detail == "word not in dictionary":
                    self.message = "Not in word list!"
                else:
                    self.message = detail
        except requests.exceptions.RequestException:
            self.message = "Network error during guess!"

    def handle_keydown(self, event):
        if event.key == pygame.K_r:
            self.start_new_game()
            return

        # 任務四：按下 H 鍵切換硬核模式開關並重開新局
        if event.key == pygame.K_h:
            self.hard_mode = not self.hard_mode
            self.start_new_game()
            return

        if self.game_over:
            return

        if event.key == pygame.K_BACKSPACE:
            if self.col > 0:
                self.col -= 1
                self.grid[self.row][self.col] = ""
        elif event.key == pygame.K_RETURN:
            self.submit_guess()
        elif event.unicode.isalpha() and len(event.unicode) == 1:
            if self.col < 5:
                self.grid[self.row][self.col] = event.unicode.upper()
                self.col += 1

    def draw(self, surface):
        surface.fill(COLOR_BG)

        # 任務四：畫面右上角顯示目前模式
        mode_text = "Mode: HARD" if self.hard_mode else "Mode: Normal"
        mode_surface = small_font.render(mode_text, True, COLOR_TEXT)
        surface.blit(mode_surface, (370, 15))

        # 繪製 6x5 網格
        margin_x, margin_y = 50, 50
        box_size = 60
        gap = 10

        for r in range(6):
            for c in range(5):
                x = margin_x + c * (box_size + gap)
                y = margin_y + r * (box_size + gap)
                rect = pygame.Rect(x, y, box_size, box_size)
                
                # 畫背景框
                pygame.draw.rect(surface, self.colors[r][c], rect, border_radius=4)
                if self.colors[r][c] == COLOR_EMPTY:
                    pygame.draw.rect(surface, (80, 80, 80), rect, width=2, border_radius=4)

                # 畫字母
                char = self.grid[r][c]
                if char:
                    text_surface = font.render(char, True, COLOR_TEXT)
                    text_rect = text_surface.get_rect(center=rect.center)
                    surface.blit(text_surface, text_rect)

        # 任務三：側邊欄 (x: 500~700 區域) 與分隔線
        pygame.draw.line(surface, COLOR_LINE, (500, 0), (500, HEIGHT), 2)
        sidebar_rect = pygame.Rect(502, 0, 198, HEIGHT)
        pygame.draw.rect(surface, COLOR_PANEL_BG, sidebar_rect)

        # 任務三：側邊欄上方顯示勝率資訊 Total: X | Wins: Y | Win Rate: Z%
        total = self.stats.get("total_games", 0)
        wins = self.stats.get("wins", 0)
        rate = self.stats.get("win_rate", 0)
        stats_str = f"Total: {total} | Wins: {wins} | Win Rate: {rate}%"
        stats_surface = small_font.render(stats_str, True, COLOR_TEXT)
        surface.blit(stats_surface, (510, 20))

        # 任務三：側邊欄歷史紀錄面板標題與猜過單字列表
        hist_title = sidebar_font.render("History", True, COLOR_TEXT)
        surface.blit(hist_title, (510, 60))

        for idx, word in enumerate(self.history):
            h_surface = sidebar_font.render(f"{idx + 1}. {word}", True, COLOR_TEXT)
            surface.blit(h_surface, (510, 95 + idx * 30))

        # 畫底部提示訊息
        msg_surface = small_font.render(self.message, True, COLOR_TEXT)
        msg_rect = msg_surface.get_rect(center=(250, HEIGHT - 40))
        surface.blit(msg_surface, msg_rect)

def main():
    clock = pygame.time.Clock()
    game = WordleGame()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                game.handle_keydown(event)

        game.draw(screen)
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()