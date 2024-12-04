import pyautogui
from loguru import logger
from PIL import ImageChops
from utils import (
    locate,
    scroll_down_only_move,
    click_and_return,
    game_screenshot,
    focus_game_window,
    close_game_window,
    save_game_screenshot,
    focus_magic_online,
)
from find import (
    get_next_icon_center,
    scroll_to_top_of_event_history,
    get_match_details,
    get_games_list,
    get_match_list,
    go_to_game_history,
)
from ocr import get_game_ended_on_box
import time
import keyboard
import os

positions = {
    'settings': (1174, 40),
    'game_history': (63, 280),
    'test_game_details': (903, 270),
    'test_game_replay_start': (721, 322),
    'next': (619, 962),
    'mouse_pos_for_scroll': (1207, 245)
}
event_scroll = (846, 325)
match_history_box = (204, 255, 1219, 796)
match_x_coords = {
    'game_type': (223, 321),
    'format': (324, 415),
    'screen_name': (428, 608),
    'result': (621, 715),
    'date': (721, 873)
}


event_history_box = (601, 264, 847, 576)
game_has_ended_box = (18, 413, 133, 435)


def next():
    original_pos = pyautogui.position()
    center = get_next_icon_center()
    if not center:
        logger.debug('Next icon not found')
        return
    pyautogui.click(*center)
    pyautogui.moveTo(*original_pos)


class GameRecording():
    def __init__(self, matchup: dict, game: dict):
        self.previous_ss = game_screenshot()
        self.ss = self.previous_ss
        self.i = 0
        self.diff = None
        self.diff_is_zero_count = 0
        self.matchup = matchup
        self.game = game
        self.path = ''
        self.set_path()
        self.saw_game_end_count = 0

    def set_diff(self):
        self.diff = list(ImageChops.difference(self.ss, self.previous_ss).getdata())

    def check_diff(self):
        if all(p == (0, 0, 0) for p in self.diff) and self.i > 0:
            self.diff_is_zero_count += 1
            return
        else:
            self.diff_is_zero_count = 0

    def set_path(self):
        items = [
            os.getcwd(),
            'game_recordings',
            self.matchup['game_type'],
            self.matchup['format'],
            self.matchup['screen_name'],
            self.matchup['date'].replace('/', '-').replace(':', ''),
            'round_'+str(self.game['round']),
            'game_'+str(self.game['number']),
        ]
        logger.debug(items)
        self.path = os.path.join(*items) + '\\\\'
        logger.debug(self.path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def game_has_been_recorded(self):
        if not os.path.exists(self.path):
            return False
        files = os.listdir(self.path)
        return files != []

    def run(self):
        if self.game_has_been_recorded():
            logger.debug(f'Game has already been recorded at {self.path}')
            return
        start_game_replay(self.game)
        wait_for_game_to_load()
        focus_game_window()
        while True:
            if keyboard.is_pressed('k'):
                logger.debug('Keyboard interrupt is pressed, stopping')
                break
            self.ss = save_game_screenshot(f'{self.path}step_{self.i}.png')
            self.set_diff()
            self.check_diff()
            if self.diff_is_zero_count > 3:
                logger.debug(f'breaking at {self.i}, too many identical images in sequence')
                break
            if get_game_ended_on_box(game_has_ended_box):
                logger.debug(f'Game appears to have ended at {self.i}')
                self.saw_game_end_count += 1
            time.sleep(0.05)
            next()
            time.sleep(0.5)
            self.previous_ss = self.ss
            self.i += 1
            if self.saw_game_end_count > 3:
                break
        close_game_window()
        wait_for_game_to_close()


def start_game_replay(game_dict: dict):
    logger.debug(f'Starting game replay for game {game_dict}')
    scroll_to_top_of_event_history()
    time.sleep(1)
    for _ in range(game_dict['scrolls']):
        scroll_down_only_move(*event_scroll)
    time.sleep(1)
    click_and_return(*game_dict['button'])
    pyautogui.moveTo(*game_dict['button'])


def wait_for_game_to_load():
    start = time.time()
    while True:
        l1 = locate('./jobs/game_recorder/reference_imgs/next_icon.png')
        l2 = locate('./jobs/game_recorder/reference_imgs/next_icon_selected.PNG')
        l3 = locate('./jobs/game_recorder/reference_imgs/next_icon_dotted.PNG')
        if l1 or l2 or l3 or time.time() - start > 30:
            return
        time.sleep(1)


def wait_for_game_to_close():
    start = time.time()
    while True:
        l1 = locate('./jobs/game_recorder/reference_imgs/next_icon.png')
        l2 = locate('./jobs/game_recorder/reference_imgs/next_icon_selected.PNG')
        l3 = locate('./jobs/game_recorder/reference_imgs/next_icon_dotted.PNG')
        if l1 is None and l2 is None and l3 is None or time.time() - start > 30:
            return
        time.sleep(1)


if __name__ == "__main__":
    import pprint
    logger.debug('Starting game recording')
    focus_magic_online()
    go_to_game_history()
    matches = get_match_list()
    logger.debug(pprint.pformat(matches))
    for m in matches:
        get_match_details(m)
        time.sleep(1)
        games = get_games_list()
        logger.debug(pprint.pformat(games))
        for g in games:
            start_game_replay(g)
            focus_game_window()
            gr = GameRecording(m, g)
            gr.run()
    logger.debug('Game recording finished')
