import pyautogui
from utils import (
    locate,
    locate_all,
    scroll_down_only_move,
    scroll_up_only_move,
    click_and_return,
    focus_magic_online,
)
from ocr import (
    get_matchups_on_box,
    get_matchup_on_box,
    get_game_number_on_box,
    get_game_description_on_box,
)
import time
from loguru import logger
import json

CONFIG = json.load(open('config.json'))


def scroll_to_bottom_of_match_history():
    is_scrolled = locate('./jobs/game_recorder/reference_imgs/is_scrolled_down.png')
    scrolls = 0
    while not is_scrolled and scrolls < 200:
        scroll_down_only_move(*CONFIG['positions']['mouse_pos_for_scroll'])
        is_scrolled = locate('./jobs/game_recorder/reference_imgs/is_scrolled_down.png')
        scrolls += 1


def go_to_game_history():
    focus_magic_online()
    click_and_return(*CONFIG['positions']['settings'])
    time.sleep(1)
    click_and_return(*CONFIG['positions']['game_history'])
    time.sleep(1)
    scroll_to_bottom_of_match_history()


def get_last_match_y_coord():
    w = get_matchups_on_box(CONFIG['match_history_box'])
    y_coord = max(w['top']) + CONFIG['match_history_box'][1]
    return y_coord


def get_single_match(scrolls):
    y_coord = get_last_match_y_coord()
    logger.debug(y_coord)
    pyautogui.moveTo(200, y_coord + 18)
    top = y_coord - 7
    bottom = y_coord + 18
    single_match = {'scrolls': scrolls, 'top': top, 'bottom': bottom}
    for key in CONFIG['match_x_coords']:
        left, right = CONFIG['match_x_coords'][key][0], CONFIG['match_x_coords'][key][1]
        box = (left, top, right, bottom)
        single_match[key] = get_matchup_on_box(box)
    return single_match


def get_match_list():
    matches = []
    seen = set()
    counter = 0
    found_a_new_match = False
    scrolls = 0
    while counter < 3 or found_a_new_match:
        new_match = get_single_match(scrolls)
        m_name = str({k: v for k, v in new_match.items() if k != 'scrolls'})
        logger.debug(new_match)
        if m_name not in seen:
            matches.append(new_match)
            found_a_new_match = True
        else:
            found_a_new_match = False
        seen.add(m_name)
        scroll_up_only_move(*CONFIG['positions']['mouse_pos_for_scroll'])
        scrolls += 1
        counter += 1
    return matches


def get_next_icon_center():
    pos = locate('./jobs/game_recorder/reference_imgs/next_icon.png')
    pos2 = locate('./jobs/game_recorder/reference_imgs/next_icon_selected.png')
    pos3 = locate('./jobs/game_recorder/reference_imgs/next_icon_dotted.png')
    if not any([pos, pos2, pos3]):
        return None
    if pos:
        return pyautogui.center(pos)
    if pos2:
        return pyautogui.center(pos2)
    return pyautogui.center(pos3)


def event_scrollbar_exists():
    scroll_down_event_icon = locate('./jobs/game_recorder/reference_imgs/event_scrolldown_icon.PNG')
    scroll_up_event_icon = locate('./jobs/game_recorder/reference_imgs/event_scrollup_icon.PNG')
    return scroll_down_event_icon or scroll_up_event_icon


def get_league_game_list():
    locations = locate_all('./jobs/game_recorder/reference_imgs/copy_game_info_button.PNG')
    games_list = []
    for loc in locations:
        bottom = loc.top + loc.height
        game_description_box = (638, loc.top, 686, bottom)
        game_number_box = (686, loc.top, 762, bottom)
        game = {
            'ticket': get_game_number_on_box(game_number_box),
            'number': get_game_description_on_box(game_description_box).replace('Game', ''),
            'button': (loc.left, bottom + 10),
            'scrolls': 0,
            'round': 1
        }
        if game not in games_list:
            games_list.append(game)
    return games_list


def get_tourney_game_list():
    games_list = []
    seen_games = set()
    scrolls = 0
    while True:
        locations = locate_all('./jobs/game_recorder/reference_imgs/copy_game_info_button.PNG')
        appended_games = 0
        for loc in locations:
            bottom = loc.top + loc.height
            game_description_box = (638, loc.top, 686, bottom)
            game_number_box = (686, loc.top, 762, bottom)
            ticket = get_game_number_on_box(game_number_box).replace('#', '')
            number = get_game_description_on_box(game_description_box).replace('Game', '')
            button = (loc.left, bottom + 14)
            if bottom + 14 > 710:
                continue
            if not ticket or not number:
                continue
            game = {
                'ticket': int(ticket),
                'number': int(number),
                'button': button,
                'scrolls': scrolls,
            }
            game_name = str({k: v for k, v in game.items() if k != 'scrolls' and k != 'button'})
            if game_name not in seen_games:
                seen_games.add(game_name)
                games_list.append(game)
                appended_games += 1
        if appended_games == 0:
            break
        for _ in range(3):
            scroll_down_only_move(*CONFIG['event_scroll'])
            scrolls += 1
    games_list = add_rounds_to_games_list(games_list)
    return games_list


def get_games_list():
    if not event_scrollbar_exists():
        return get_league_game_list()
    return get_tourney_game_list()


def add_rounds_to_games_list(games_list):
    games_list = sorted(games_list, key=lambda x: x['ticket'])
    last_game_num = 0
    round = 1
    for i, game in enumerate(games_list):
        if game['number'] < last_game_num:
            round += 1
        last_game_num = game['number']
        games_list[i]['round'] = round
    return games_list


def get_match_details(matchup_dict: dict):
    scroll_to_bottom_of_match_history()
    for _ in range(matchup_dict['scrolls']):
        scroll_up_only_move(*CONFIG['positions']['mouse_pos_for_scroll'])
    y = (matchup_dict['top'] + matchup_dict['bottom']) // 2
    click_and_return(593, y)
    time.sleep(0.1)
    click_and_return(593, y)


def scroll_to_top_of_event_history():
    event_is_not_scrolled_to_top = locate('./jobs/game_recorder/reference_imgs/event_scrollup_icon.PNG')
    while event_is_not_scrolled_to_top is not None:
        for _ in range(3):
            scroll_up_only_move(event_is_not_scrolled_to_top.left, event_is_not_scrolled_to_top.top)
        event_is_not_scrolled_to_top = locate('./jobs/game_recorder/reference_imgs/event_scrollup_icon.PNG')
