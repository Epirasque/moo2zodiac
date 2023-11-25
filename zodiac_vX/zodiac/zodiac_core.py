import math
import sys
from os.path import isfile
from tkinter import *
from tkinter.font import Font

VERSION = "v1.0"

# TODO: use git?
# TODO: version marker into exported one
# TODO: zoom-buttons (scale-factor)
# TODO: shift everything with arrowkeys?
# ...

# GUI
STAR_RECT_RADIUS = 8
WORMHOLE_SOURCE_CIRCLE_RADIUS = 10
SCALE_FACTOR = .7
GALAXY_COLOR = '#161616'
CROSSHAIR_COLOR = '#303030'
STAR_OUTLINE_COLOR = '#454545'
NORMAL_STAR_COLOR = 'white'
HOMEWORLD_COLOR = 'burlywood3'
ORION_COLOR = 'green'
BLACK_HOLE_COLOR = 'purple'
WORMHOLE_COLOR = 'teal'
INDICATOR_COLORS = {}
#INDICATOR_COLORS['4'] = 'darkorange'
#INDICATOR_COLORS['6'] = 'darkorange1'
#INDICATOR_COLORS['9'] = 'darkorange2'
#INDICATOR_COLORS['12'] = 'darkorange3'
#INDICATOR_COLORS['14'] = 'darkorange4'
#INDICATOR_COLORS['18'] = 'firebrick4'
INDICATOR_NAMES = {}
INDICATOR_NAMES['4'] = 'Standard Fuel Cells'
INDICATOR_NAMES['6'] = 'Deuterium / Standard + Extended Tank'
INDICATOR_NAMES['9'] = 'Iridium / Deuterium + Extended Tank'
INDICATOR_NAMES['12'] = '12 Parsecs: Uridium'
INDICATOR_NAMES['14'] = '14 Parsecs: Iridium + Extended Tank'
INDICATOR_NAMES['18'] = '18 Parsecs: Uridium + Extended Tank'

HIGHEST_PARSEC_INDICATOR_RANGE = 18

# FILE HANDLING
TEMPLATE_DRAWN_STARS_MARKER = '#DRAWN_SYSTEMS_MARKER#'
TEMPLATE_SAVESLOT_MARKER = '#SAVESLOT_MARKER#'
TITLE_MARKER = '#TITLE_MARKER#'
GALAXY_SIZE_MARKER = '#GALAXY_SIZE_MARKER#'
VERSION_MARKER = '#VERSION_MARKER#'

# ENCODINGS / NAMES
NORMAL_STAR = 'Normal System'
HOMEWORLD = 'Homeworld'
ORION = 'Orion'
BLACK_HOLE = 'Black Hole'
GALAXY_SMALL = 'Small Galaxy'
GALAXY_MEDIUM = 'Medium Galaxy'
GALAXY_LARGE = 'Large / Cluster Galaxy'
GALAXY_HUGE = 'Huge Galaxy'
SET_WORMHOLE = 'Set Wormhole'
CLEAR_WORMHOLE = 'Remove Wormhole'
MODE_PLACE_WORMHOLE_A = 'whA'
MODE_PLACE_WORMHOLE_B = 'whB'
STARS_REMAINING = 'Stars Remaining:'
NORMALS_PLACED = 'Normal Systems:'
HOMEWORLDS_PLACED = 'Possible Homeworld Locations:'
ORIONS_PLACED = 'Possible Orion Locations:'
BLACK_HOLES_PLACED = 'Black Holes:'
WORMHOLES_PLACED = 'Wormholes:'


class SystemClickmode:
    def __init__(self, mode, canvas):
        self.mode = mode
        self.canvas = canvas
        self.currentArguments = {}
        self.canvasMarkers = []

    def reset(self):
        for canvas_object in self.canvas.find_all():
            for marker in self.canvasMarkers:
                if canvas_object == marker:
                    self.canvas.delete(canvas_object)
        self.currentArguments = {}
        self.canvasMarkers = []


class Galaxy:
    def __init__(self, size_description, width, height, nr_stars, radio_button_id):
        self.size_description = size_description
        self.width = width
        self.height = height
        self.nr_stars = nr_stars
        self.radio_button_id = radio_button_id


class Star:
    def __init__(self, x, y, starType, drawn_star):
        self.x = round(x / SCALE_FACTOR)
        self.y = round(y / SCALE_FACTOR)
        self.canvas_x = x
        self.canvas_y = y
        self.starType = starType
        self.drawn_star = drawn_star
        self.wormhole_partner = None
        self.wormhole = None
        self.wormholeMarker = None

    def delete(self, canvas):
        canvas.delete(self.drawn_star)
        if self.wormholeMarker is not None:
            canvas.delete(self.wormholeMarker)
        self.dissolve_wormhole()

    def dissolve_wormhole(self):
        if self.wormhole_partner is not None:
            self.wormhole.delete_canvas_line()
            self.wormhole_partner.wormhole_partner = None
            self.wormhole_partner.wormhole = None
        self.wormhole_partner = None
        self.wormhole = None

    def __str__(self):
        return f'{self.starType.name}, {self.x}, {self.y}, {self.wormhole}'


class StarType:
    def __init__(self, name, draw_color):
        self.name = name
        self.draw_color = draw_color


class Wormhole:
    def __init__(self, source, target, canvas_line, canvas):
        self.source = source
        self.target = target
        self.canvas_line = canvas_line
        self.canvas = canvas
        source.wormhole_partner = target
        target.wormhole_partner = source
        source.wormhole = self
        target.wormhole = self

    def delete_canvas_line(self):
        self.canvas.delete(self.canvas_line)

    def __str__(self):
        return f'Wormhole with length {math.dist([self.source.y, self.source.x], [self.target.y, self.target.x])}'


class Settings:
    def __init__(self, starType, galaxy, systemClickmode, galaxy_radio, parsec_indicator_toggles, mirror_mode):
        self.starType = starType
        self.galaxy = galaxy
        self.systemClickmode = systemClickmode
        self.galaxy_radio = galaxy_radio
        self.blockOneClick = False
        self.parsec_indicator_toggles = parsec_indicator_toggles
        self.mirror_mode = mirror_mode

    def setStarType(self, starType):
        self.starType = starType

    def setGalaxy(self, galaxy):
        self.galaxy = galaxy
        self.galaxy_radio.set(galaxy.radio_button_id)

    def setSystemClickmode(self, systemClickmode):
        self.systemClickmode.reset()
        systemClickmode.reset()
        self.systemClickmode = systemClickmode


stat_labels = {}  # not technically constant
SYSTEM_CLICK_MODES = {}
GALAXIES = {}
GALAXIES[GALAXY_SMALL] = Galaxy(GALAXY_SMALL, 506, 400, 20, 0)
GALAXIES[GALAXY_MEDIUM] = Galaxy(GALAXY_MEDIUM, 759, 600, 36, 1)
GALAXIES[GALAXY_LARGE] = Galaxy(GALAXY_LARGE, 1012, 800, 54, 2)
GALAXIES[GALAXY_HUGE] = Galaxy(GALAXY_HUGE, 1518, 1200, 71, 3)
STAR_TYPES = {}
STAR_TYPES[NORMAL_STAR] = StarType(NORMAL_STAR, NORMAL_STAR_COLOR)
STAR_TYPES[HOMEWORLD] = StarType(HOMEWORLD, HOMEWORLD_COLOR)
STAR_TYPES[ORION] = StarType(ORION, ORION_COLOR)
STAR_TYPES[BLACK_HOLE] = StarType(BLACK_HOLE, BLACK_HOLE_COLOR)


def get_parsec_indicator_color(radius_in_parsec):
    if str(radius_in_parsec) in INDICATOR_COLORS:
        color = INDICATOR_COLORS[str(radius_in_parsec)]
    else:
        min_index = 1
        max_index = 13
        if radius_in_parsec == 12:
            used_index = 11
        elif radius_in_parsec == 14:
            used_index = 12
        elif radius_in_parsec == 16:
            used_index = 13
        else:
            used_index = radius_in_parsec
        dx = 0.8
        f = (used_index - min_index) / (1. + (max_index - min_index))
        if f < 0:
            f = 0.
        if f > 1:
            f = 1.
        g = (6. - 2. * dx ) * f + dx
        # inverted rainbow scale
        B = max(0., (3. - abs(g - 4.) - abs(g - 5.)) / 2.)
        G = max(0., (4. - abs(g - 2.) - abs(g - 4.)) / 2.)
        R = max(0., (3. - abs(g - 1.) - abs(g - 2.)) / 2.)
        contrasting_font_color = 'black' if R + G + B > 1.1 else 'white'
        B_hex = hex(round(255. * B))[2:]
        G_hex = hex(round(255. * G))[2:]
        R_hex = hex(round(255. * R))[2:]
        if len(B_hex) == 1:
            B_hex = f'0{B_hex}'
        if len(G_hex) == 1:
            G_hex = f'0{G_hex}'
        if len(R_hex) == 1:
            R_hex = f'0{R_hex}'
        #hex_channel_color = hex(round(15 * (17 - radius_in_parsec)))[2:]
        color = f'#{R_hex}{G_hex}{B_hex}'
    return color, contrasting_font_color


def refresh_marker_layer_order(canvas):
    for layer_behind_new_object in range(1, HIGHEST_PARSEC_INDICATOR_RANGE + 1):
        try:
            canvas.tag_lower(f'parsec_indicator_{layer_behind_new_object}', f'parsec_indicator')
        except:
            pass


def clear_galaxy(canvas, all_stars, settings):
    for star in all_stars:
        star.delete(canvas)
    all_stars.clear()
    settings.setSystemClickmode(SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A])
    update_stats(all_stars, settings)


def remove_star(canvas, star, all_stars, settings):
    star.delete(canvas)
    all_stars.remove(star)
    settings.setSystemClickmode(SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A])
    update_stats(all_stars, settings)


def change_galaxy_size(canvas, settings, galaxy, all_stars, crosshair):
    settings.setGalaxy(galaxy)
    canvas_width = round(galaxy.width * SCALE_FACTOR)
    canvas_height = round(galaxy.height * SCALE_FACTOR)
    canvas.config(width=canvas_width, height=canvas_height)
    clear_galaxy(canvas, all_stars, settings)
    settings.setSystemClickmode(SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A])
    canvas.moveto(crosshair['vertical'], round(canvas_width / 2 - 1.5), 0)
    canvas.moveto(crosshair['horizontal'], 0, round(canvas_height / 2 - 1.5))


def create_wormhole(source, target, canvas, all_stars, settings):
    canvas_line = canvas.create_line(source.canvas_x, source.canvas_y, target.canvas_x, target.canvas_y,
                                     fill=WORMHOLE_COLOR, width=3)
    canvas.tag_lower(canvas_line)
    try:
        canvas.tag_raise(canvas_line, f'parsec_indicator')
    except:
        pass
    source.dissolve_wormhole()
    target.dissolve_wormhole()
    Wormhole(source, target, canvas_line, canvas)
    update_stats(all_stars, settings)


def leftclick_star(canvas, star, settings, all_stars):
    settings.blockOneClick = True
    if settings.systemClickmode.mode == MODE_PLACE_WORMHOLE_A:
        settings.setSystemClickmode(SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_B])
        source_marker = canvas.create_oval(star.canvas_x - WORMHOLE_SOURCE_CIRCLE_RADIUS,
                                           star.canvas_y - WORMHOLE_SOURCE_CIRCLE_RADIUS,
                                           star.canvas_x + WORMHOLE_SOURCE_CIRCLE_RADIUS,
                                           star.canvas_y + WORMHOLE_SOURCE_CIRCLE_RADIUS,
                                           outline=WORMHOLE_COLOR, width=3)
        canvas.tag_lower(source_marker)
        try:
            canvas.tag_raise(source_marker, f'parsec_indicator')
        except:
            pass
        settings.systemClickmode.currentArguments['source'] = star
        settings.systemClickmode.canvasMarkers.append(source_marker)
        star.wormholeMarker = source_marker
    elif settings.systemClickmode.mode == MODE_PLACE_WORMHOLE_B:
        source = settings.systemClickmode.currentArguments['source']
        print('Wormhole from ' + str(source) + " to " + str(star))
        settings.setSystemClickmode(SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A])
        # TODO: prevent orion-wormholes? TODO: try out what happens if wormholes to blackholes are allowed!
        if source != star and source.starType != STAR_TYPES[BLACK_HOLE] and star.starType != STAR_TYPES[BLACK_HOLE]:
            create_wormhole(source, star, canvas, all_stars, settings)
        else:
            print('Ignoring wormhole attempt: source and target are identical')


def add_single_star(x, y, canvas, all_stars, settings):
    starType = settings.starType
    polygon_points = [x - STAR_RECT_RADIUS, y,
                      x, y - STAR_RECT_RADIUS,
                      x + STAR_RECT_RADIUS, y,
                      x, y + STAR_RECT_RADIUS]
    drawn_star = canvas.create_polygon(polygon_points, fill=starType.draw_color, outline=STAR_OUTLINE_COLOR)
    #drawn_star = canvas.create_rectangle((event.x - STAR_RECT_RADIUS, event.y - STAR_RECT_RADIUS),
    #                                     (event.x + STAR_RECT_RADIUS, event.y + STAR_RECT_RADIUS),
    #                                     fill=starType.draw_color)
    star = Star(x, y, starType, drawn_star)
    all_stars.append(star)
    refresh_marker_layer_order(canvas)
    canvas.tag_bind(drawn_star, '<Button-1>',
                    lambda star_clicked_event: leftclick_star(canvas, star, settings, all_stars))
    canvas.tag_bind(drawn_star, '<Button-3>', lambda delete_event: remove_star(canvas, star, all_stars, settings))


def add_stars(event, canvas, all_stars, settings):
    mirror_horizontally = settings.mirror_mode['horizontal'].get()
    mirror_vertically = settings.mirror_mode['vertical'].get()
    if len(all_stars) + 1 * (1 + mirror_horizontally) * (1 + mirror_vertically) > settings.galaxy.nr_stars:
        print(f'Trying to exceed maximum number of stars for given galaxy size: {settings.galaxy.nr_stars}')
        return
    if settings.blockOneClick:
        settings.blockOneClick = False
        return
    x = event.x
    y = event.y
    add_single_star(x, y, canvas, all_stars, settings)
    if mirror_horizontally:
        add_single_star(canvas.winfo_width() - x, y, canvas, all_stars, settings)
    if mirror_vertically:
        add_single_star(x, canvas.winfo_height() - y, canvas, all_stars, settings)
    if mirror_horizontally and mirror_vertically:
        add_single_star(canvas.winfo_width() - x, canvas.winfo_height() - y, canvas, all_stars, settings)
    update_stats(all_stars, settings)


def format_star_output(all_stars):
    output = ''
    for star in all_stars:
        if star.wormhole_partner is not None:
            output += f'{{star_type=\'{star.starType.name}\', x={star.x}, y={star.y}, wormhole_partner_x={star.wormhole_partner.x}, wormhole_partner_y={star.wormhole_partner.y}}}, '
        else:
            output += f'{{star_type=\'{star.starType.name}\', x={star.x}, y={star.y}}}, '
    output = output[:-2]
    print(output)
    return output


def export_map(all_stars, title_entry, save_slot, galaxy, load_button):
    nr_stars = len(all_stars)
    title = title_entry.get()
    galaxy_size = galaxy.size_description
    print(f'Exporting {nr_stars} stars for slot {save_slot}...')
    saveslot_output = f'{save_slot}'
    star_output = format_star_output(all_stars)
    with open('ZODIAC_TEMPLATE.CFG', 'r') as template_file:
        with open(f'ZODIAC{save_slot}.CFG', 'w') as file_to_save:
            for line in template_file:
                if TEMPLATE_SAVESLOT_MARKER in line:
                    line = line.replace(TEMPLATE_SAVESLOT_MARKER, saveslot_output)
                if TITLE_MARKER in line:
                    line = line.replace(TITLE_MARKER, title)
                if VERSION_MARKER in line:
                    line = line.replace(VERSION_MARKER, VERSION)
                file_to_save.write(line)
    with open('ZODIAC_TEMPLATE.LUA', 'r') as template_file:
        with open(f'ZODIAC{save_slot}.LUA', 'w') as file_to_save:
            for line in template_file:
                if TEMPLATE_DRAWN_STARS_MARKER in line:
                    line = line.replace(TEMPLATE_DRAWN_STARS_MARKER, star_output)
                if TITLE_MARKER in line:
                    line = line.replace(TITLE_MARKER, title)
                if GALAXY_SIZE_MARKER in line:
                    line = line.replace(GALAXY_SIZE_MARKER, galaxy_size)
                if VERSION_MARKER in line:
                    line = line.replace(VERSION_MARKER, VERSION)
                file_to_save.write(line)
    load_button.config(state=NORMAL)
    load_button.select()


def import_map(all_stars, title_entry, save_slot, settings, canvas, crosshair):
    galaxy_size_line = None
    title_line = None
    systems_line = None
    filename = f'ZODIAC{save_slot}.LUA'
    if not isfile(filename):
        print(f'Cannot load {filename}, file not found')
        return
    with open(filename, 'r') as file_to_load:
        for line in file_to_load:
            # checks are not very robust against changes but that's ok, TODO: add disclaimer
            if 'GALAXY_SIZE=' in line:
                galaxy_size_line = line
            elif 'TITLE=' in line:
                title_line = line
            elif 'star_type=' in line:
                systems_line = line
            if galaxy_size_line is not None and title_line is not None and systems_line is not None:
                break
    loaded_galaxy_size_string = galaxy_size_line.strip().split('=')[1].strip().replace('\'', '')
    loaded_title_string = title_line.strip().split('=')[1].strip().replace('\'', '')
    loaded_systems_strings = systems_line.strip().split('}, {')
    print('Loaded values:')
    print(f'Title: \'{loaded_title_string}\'')
    print(f'Galaxy_Size: \'{loaded_galaxy_size_string}\'')
    print(f'Systems:')
    for loaded_system_string in loaded_systems_strings:
        print(f'\'{loaded_system_string}\'')
    title_entry.delete(0, len(title_entry.get()))
    title_entry.insert(0, loaded_title_string)
    change_galaxy_size(canvas, settings, GALAXIES[loaded_galaxy_size_string], all_stars, crosshair)
    for loaded_system_string in loaded_systems_strings:
        system_parameters = loaded_system_string.replace('}', '').replace('{', '').split(', ')
        settings.starType = STAR_TYPES[system_parameters[0].split('=')[1].replace('\'', '')]
        addStarEvent = Event()
        addStarEvent.x = round(int(system_parameters[1].split('=')[1]) * SCALE_FACTOR)
        addStarEvent.y = round(int(system_parameters[2].split('=')[1]) * SCALE_FACTOR)
        add_stars(addStarEvent, canvas, all_stars, settings)

    # ensure all stars exist before creating wormholes, still better than searching for non-existing stars
    for loaded_system_string in loaded_systems_strings:
        system_parameters = loaded_system_string.replace('}', '').replace('{', '').split(', ')
        if len(system_parameters) > 3:
            found = False
            source_x = int(system_parameters[1].split('=')[1])
            source_y = int(system_parameters[2].split('=')[1])
            target_x = int(system_parameters[3].split('=')[1])
            target_y = int(system_parameters[4].split('=')[1])
            for source in all_stars:
                if source.wormhole_partner is None and source.x == source_x and source.y == source_y:
                    for target in all_stars:
                        if target.wormhole_partner is None and target.x == target_x and target.y == target_y:
                            found = True
                            create_wormhole(source, target, canvas, all_stars, settings)
                            break
                if found == True:
                    break


def update_stats(all_stars, settings):
    stat_labels[STARS_REMAINING].config(
        text=f'{settings.galaxy.nr_stars - len(all_stars)} / {settings.galaxy.nr_stars}')
    stat_labels[NORMALS_PLACED].config(
        text=f'{int(sum(star.starType == STAR_TYPES[NORMAL_STAR] for star in all_stars))}')
    stat_labels[HOMEWORLDS_PLACED].config(
        text=f'{int(sum(star.starType == STAR_TYPES[HOMEWORLD] for star in all_stars))}')
    stat_labels[ORIONS_PLACED].config(
        text=f'{int(sum(star.starType == STAR_TYPES[ORION] for star in all_stars))}')
    stat_labels[BLACK_HOLES_PLACED].config(
        text=f'{int(sum(star.starType == STAR_TYPES[BLACK_HOLE] for star in all_stars))}')
    stat_labels[WORMHOLES_PLACED].config(
        text=f'{int(sum(star.wormhole_partner is not None for star in all_stars) / 2)}')


def change_parsec_indicator(canvas, parsecIndicators, radius_in_parsec, parsec_indicator_toggles):
    if parsec_indicator_toggles[str(radius_in_parsec)].get():
        enable_parsec_indicator(canvas, parsecIndicators, radius_in_parsec)
    else:
        disable_parsec_indicator(canvas, parsecIndicators, radius_in_parsec)
    refresh_marker_layer_order(canvas)


def enable_parsec_indicator(canvas, parsecIndicators, radius_in_parsec):
    radius_in_scaled_coordinates = round(parsec2distance(radius_in_parsec) * SCALE_FACTOR)
    indicator_color, contrasting_font_color = get_parsec_indicator_color(radius_in_parsec)
    indicator = canvas.create_oval(- radius_in_scaled_coordinates, - radius_in_scaled_coordinates,
                                   radius_in_scaled_coordinates, radius_in_scaled_coordinates,
                                   fill=indicator_color, width=2,
                                   tags=('parsec_indicator', f'parsec_indicator_{radius_in_parsec}'))
    canvas.lower(indicator)
    parsecIndicators[radius_in_parsec] = indicator


def disable_parsec_indicator(canvas, parsecIndicators, radius_in_parsec):
    canvas.delete(parsecIndicators[radius_in_parsec])
    del parsecIndicators[radius_in_parsec]


def parsec2distance(parsec):
    return parsec * 30 - 2


def main(argv):
    root = Tk()
    root.title(f'Zodiac {VERSION} (by Epirasque -> romanhable@web.de)')
    button_window = Frame(root)
    button_window.grid(row=0, column=0, sticky='nwse')

    canvas_width = round(GALAXIES[GALAXY_HUGE].width * SCALE_FACTOR)
    canvas_height = round(GALAXIES[GALAXY_HUGE].height * SCALE_FACTOR)

    canvas_frame = Frame(root)
    canvas_frame.grid(row=0, column=1, sticky="nswe")

    canvas_header_frame = Frame(canvas_frame)
    canvas_header_frame.grid(row=0, column=0, sticky="nswe")

    canvas = Canvas(canvas_frame, width=canvas_width, height=canvas_height, bg=GALAXY_COLOR)
    SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A] = SystemClickmode(MODE_PLACE_WORMHOLE_A, canvas)
    SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_B] = SystemClickmode(MODE_PLACE_WORMHOLE_B, canvas)

    app_width = canvas_width + 400 + 80
    app_height = canvas_height + 50 + 60

    root.geometry(f'{app_width}x{app_height}+50+20')
    root.resizable(True, True)

    all_stars = []
    parsec_indicator_toggles = {}

    crosshair_vertical = canvas.create_line(canvas_width / 2, 0, canvas_width / 2, canvas_height,
                                            fill=CROSSHAIR_COLOR, width=3)
    crosshair_horizontal = canvas.create_line(0, canvas_height / 2, canvas_width, canvas_height / 2,
                                              fill=CROSSHAIR_COLOR, width=3)
    crosshair = {'vertical': crosshair_vertical, 'horizontal': crosshair_horizontal}
    canvas.moveto(crosshair['vertical'], round(canvas_width / 2 - 1.5), 0)
    canvas.moveto(crosshair['horizontal'], 0, round(canvas_height / 2 - 1.5))

    Label(button_window, text='GALAXY SIZE', relief=GROOVE) \
        .grid(row=0, column=0, sticky=W, padx=5, pady=5)
    galaxy_radio = IntVar()
    galaxy_radio.set(3)

    mirror_horizontally = BooleanVar()
    mirror_vertically = BooleanVar()
    mirror_mode = {'horizontal': mirror_horizontally, 'vertical': mirror_vertically}
    settings = Settings(STAR_TYPES[NORMAL_STAR], GALAXIES[GALAXY_HUGE], SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A],
                        galaxy_radio, parsec_indicator_toggles, mirror_mode)

    Radiobutton(button_window, text=GALAXY_SMALL, indicatoron=False, variable=galaxy_radio, value=0,
                activebackground=GALAXY_COLOR, bg=GALAXY_COLOR, selectcolor=GALAXY_COLOR,
                fg='white', activeforeground='white',
                command=lambda: change_galaxy_size(canvas, settings, GALAXIES[GALAXY_SMALL], all_stars, crosshair)) \
        .grid(row=1, column=0, sticky=W, padx=5, pady=5)
    Radiobutton(button_window, text=GALAXY_MEDIUM, indicatoron=False, variable=galaxy_radio, value=1,
                activebackground=GALAXY_COLOR, bg=GALAXY_COLOR, selectcolor=GALAXY_COLOR,
                fg='white', activeforeground='white',
                command=lambda: change_galaxy_size(canvas, settings, GALAXIES[GALAXY_MEDIUM], all_stars, crosshair)) \
        .grid(row=2, column=0, sticky=W, padx=5, pady=5)
    Radiobutton(button_window, text=GALAXY_LARGE, indicatoron=False, variable=galaxy_radio, value=2,
                activebackground=GALAXY_COLOR, bg=GALAXY_COLOR, selectcolor=GALAXY_COLOR,
                fg='white', activeforeground='white',
                command=lambda: change_galaxy_size(canvas, settings, GALAXIES[GALAXY_LARGE], all_stars, crosshair)) \
        .grid(row=3, column=0, sticky=W, padx=5, pady=5)
    Radiobutton(button_window, text=GALAXY_HUGE, indicatoron=False, variable=galaxy_radio, value=3,
                activebackground=GALAXY_COLOR, bg=GALAXY_COLOR, selectcolor=GALAXY_COLOR,
                fg='white', activeforeground='white',
                command=lambda: change_galaxy_size(canvas, settings, GALAXIES[GALAXY_HUGE], all_stars, crosshair)) \
        .grid(row=4, column=0, sticky=W, padx=5, pady=5)

    Label(button_window, text='PLACEMENT TYPE', relief=GROOVE) \
        .grid(row=5, column=0, sticky=W, padx=5, pady=5)
    star_type_radio = IntVar()
    star_type_radio.set(0)
    Radiobutton(button_window, text=NORMAL_STAR, indicatoron=False, variable=star_type_radio, value=0,
                activebackground=NORMAL_STAR_COLOR, bg=NORMAL_STAR_COLOR, selectcolor=NORMAL_STAR_COLOR,
                command=lambda: settings.setStarType(STAR_TYPES[NORMAL_STAR])) \
        .grid(row=6, column=0, sticky=W, padx=5, pady=5)
    Radiobutton(button_window, text=HOMEWORLD, indicatoron=False, variable=star_type_radio, value=1,
                activebackground=HOMEWORLD_COLOR, bg=HOMEWORLD_COLOR, selectcolor=HOMEWORLD_COLOR,
                command=lambda: settings.setStarType(STAR_TYPES[HOMEWORLD])) \
        .grid(row=7, column=0, sticky=W, padx=5, pady=5)
    Radiobutton(button_window, text=ORION, indicatoron=False, variable=star_type_radio, value=2,
                activebackground=ORION_COLOR, bg=ORION_COLOR, selectcolor=ORION_COLOR,
                fg='white', activeforeground='white',
                command=lambda: settings.setStarType(STAR_TYPES[ORION])) \
        .grid(row=8, column=0, sticky=W, padx=5, pady=5)
    Radiobutton(button_window, text=BLACK_HOLE, indicatoron=False, variable=star_type_radio, value=3,
                activebackground=BLACK_HOLE_COLOR, bg=BLACK_HOLE_COLOR, selectcolor=BLACK_HOLE_COLOR,
                fg='white', activeforeground='white',
                command=lambda: settings.setStarType(STAR_TYPES[BLACK_HOLE])) \
        .grid(row=9, column=0, sticky=W, padx=5, pady=5)

    Label(button_window, text='MIRROR PLACEMENTS', relief=GROOVE) \
        .grid(row=10, column=0, sticky=W, padx=5, pady=5)

    Checkbutton(button_window, text='Mirror Horizontally', indicatoron=False, variable=mirror_horizontally,
                activebackground='cadetblue1', bg='cadetblue1', selectcolor='cadetblue1') \
        .grid(row=11, column=0, sticky=W, padx=5, pady=5)

    Checkbutton(button_window, text='Mirror Vertically', indicatoron=False, variable=mirror_vertically,
                activebackground='cadetblue1', bg='cadetblue1', selectcolor='cadetblue1') \
        .grid(row=12, column=0, sticky=W, padx=5, pady=5)

    Label(button_window, text='RANGE INDICATORS', relief=GROOVE) \
        .grid(row=13, column=0, sticky=W, padx=5, pady=5)
    parsec_indicator_toggles['1'] = BooleanVar()  # 1 Parsec (singular) has different text
    parsecIndicators = {}
    button_color, contrasting_font_color = get_parsec_indicator_color(1)
    Checkbutton(button_window, text='1 Parsec', indicatoron=False, variable=parsec_indicator_toggles['1'],
                activebackground=button_color, bg=button_color, selectcolor=button_color,
                fg=contrasting_font_color, activeforeground=contrasting_font_color,
                command=lambda: change_parsec_indicator(canvas, parsecIndicators, 1, parsec_indicator_toggles)) \
        .grid(row=14, column=0, sticky=W, padx=5, pady=5)
    for parsec_radius in range(2, 10 + 1):
        parsec_radius_str = str(parsec_radius)
        parsec_indicator_toggles[parsec_radius_str] = BooleanVar()
        button_display_name = f'{parsec_radius_str} Parsecs'
        if parsec_radius_str in INDICATOR_NAMES:
            button_display_name += ': ' + INDICATOR_NAMES[parsec_radius_str]
        button_color, contrasting_font_color = get_parsec_indicator_color(parsec_radius)
        Checkbutton(button_window, text=button_display_name, indicatoron=False,
                    variable=parsec_indicator_toggles[parsec_radius_str],
                    activebackground=button_color, bg=button_color, selectcolor=button_color,
                    fg=contrasting_font_color, activeforeground=contrasting_font_color,
                    command=lambda parsec_radius=parsec_radius: change_parsec_indicator(canvas, parsecIndicators,
                                                                                        parsec_radius,
                                                                                        parsec_indicator_toggles)) \
            .grid(row=14 + parsec_radius, column=0, sticky=W, padx=5, pady=5)
    parsec_indicator_toggles['12'] = BooleanVar()
    button_color, contrasting_font_color = get_parsec_indicator_color(12)
    Checkbutton(button_window, text=INDICATOR_NAMES['12'], indicatoron=False, variable=parsec_indicator_toggles['12'],
                activebackground=button_color, bg=button_color, selectcolor=button_color,
                fg=contrasting_font_color, activeforeground=contrasting_font_color,
                command=lambda: change_parsec_indicator(canvas, parsecIndicators, 12, parsec_indicator_toggles)) \
        .grid(row=25, column=0, sticky=W, padx=5, pady=5)
    parsec_indicator_toggles['14'] = BooleanVar()
    button_color, contrasting_font_color = get_parsec_indicator_color(14)
    Checkbutton(button_window, text=INDICATOR_NAMES['14'], indicatoron=False, variable=parsec_indicator_toggles['14'],
                activebackground=button_color, bg=button_color, selectcolor=button_color,
                fg=contrasting_font_color, activeforeground=contrasting_font_color,
                command=lambda: change_parsec_indicator(canvas, parsecIndicators, 14, parsec_indicator_toggles)) \
        .grid(row=26, column=0, sticky=W, padx=5, pady=5)
    parsec_indicator_toggles['18'] = BooleanVar()
    button_color, contrasting_font_color = get_parsec_indicator_color(18)
    Checkbutton(button_window, text=INDICATOR_NAMES['18'], indicatoron=False, variable=parsec_indicator_toggles['18'],
                activebackground=button_color, bg=button_color, selectcolor=button_color,
                fg=contrasting_font_color, activeforeground=contrasting_font_color,
                command=lambda: change_parsec_indicator(canvas, parsecIndicators, 18, parsec_indicator_toggles)) \
        .grid(row=27, column=0, sticky=W, padx=5, pady=5)

    Label(canvas_header_frame, text='Galaxy Title').grid(row=0, column=0, sticky=W, padx=1, pady=5)
    title_entry = Entry(canvas_header_frame, width=20)
    title_entry.grid(row=0, column=1, sticky=W, padx=1, pady=5)
    title_entry.insert(0, 'My Zodiac Galaxy')

    bold_font = Font(weight="bold")

    Label(canvas_header_frame, text=STARS_REMAINING).grid(row=0, column=2, sticky=W, padx=1, pady=5)
    stat_labels[STARS_REMAINING] = Label(canvas_header_frame, text='??/??', font=bold_font)
    stat_labels[STARS_REMAINING].grid(row=0, column=3, sticky=W, padx=1, pady=5)
    Label(canvas_header_frame, text=NORMALS_PLACED).grid(row=0, column=4, sticky=W, padx=1, pady=5)
    stat_labels[NORMALS_PLACED] = Label(canvas_header_frame, text='?', font=bold_font, bg=NORMAL_STAR_COLOR)
    stat_labels[NORMALS_PLACED].grid(row=0, column=5, sticky=W, padx=1, pady=5)
    Label(canvas_header_frame, text=HOMEWORLDS_PLACED).grid(row=0, column=6, sticky=W, padx=1, pady=5)
    stat_labels[HOMEWORLDS_PLACED] = Label(canvas_header_frame, text='?', font=bold_font, fg='white',
                                           bg=HOMEWORLD_COLOR)
    stat_labels[HOMEWORLDS_PLACED].grid(row=0, column=7, sticky=W, padx=1, pady=5)
    Label(canvas_header_frame, text=ORIONS_PLACED).grid(row=0, column=8, sticky=W, padx=1, pady=5)
    stat_labels[ORIONS_PLACED] = Label(canvas_header_frame, text='?', font=bold_font, fg='white', bg=ORION_COLOR)
    stat_labels[ORIONS_PLACED].grid(row=0, column=9, sticky=W, padx=1, pady=5)
    Label(canvas_header_frame, text=BLACK_HOLES_PLACED).grid(row=0, column=10, sticky=W, padx=1, pady=5)
    stat_labels[BLACK_HOLES_PLACED] = Label(canvas_header_frame, text='?', font=bold_font, fg='white',
                                            bg=BLACK_HOLE_COLOR)
    stat_labels[BLACK_HOLES_PLACED].grid(row=0, column=11, sticky=W, padx=1, pady=5)
    Label(canvas_header_frame, text=WORMHOLES_PLACED).grid(row=0, column=12, sticky=W, padx=1, pady=5)
    stat_labels[WORMHOLES_PLACED] = Label(canvas_header_frame, text='?', font=bold_font, fg='white', bg=WORMHOLE_COLOR)
    stat_labels[WORMHOLES_PLACED].grid(row=0, column=13, sticky=W, padx=1, pady=5)

    update_stats(all_stars, settings)

    load_radio = IntVar()
    for save_slot in range(10):
        # save_slot=save_slot prevents the value to be evaluated/overwritten later on
        load_button = Radiobutton(button_window, text=f'Load ZODIAC{save_slot}', indicatoron=False, variable=load_radio,
                                  value=save_slot,
                                  command=lambda save_slot=save_slot: import_map(all_stars, title_entry, save_slot,
                                                                                 settings, canvas, crosshair))
        load_button.grid(row=save_slot, column=3, sticky=W, padx=5, pady=5)
        if not isfile(f'ZODIAC{save_slot}.LUA'):
            load_button.config(state=DISABLED)

        Button(button_window, text=f'Save ZODIAC{save_slot}', command=lambda save_slot=save_slot, load_button=load_button:
        export_map(all_stars, title_entry, save_slot, settings.galaxy, load_button)) \
            .grid(row=save_slot, column=2, sticky=W, padx=5, pady=5)

    canvas.grid(row=1, column=0, sticky=NW)
    canvas.bind('<Button-1>', lambda add_event: add_stars(add_event, canvas, all_stars, settings))

    def getPosition(event):
        x = canvas.winfo_pointerx() - canvas.winfo_rootx()
        y = canvas.winfo_pointery() - canvas.winfo_rooty()
        for radius_in_parsec, indicator in parsecIndicators.items():
            radius_in_scaled_coordinates = round(parsec2distance(radius_in_parsec) * SCALE_FACTOR)
            canvas.moveto(indicator, x - radius_in_scaled_coordinates, y - radius_in_scaled_coordinates)

    canvas.bind('<Motion>', getPosition)

    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    finally:
        root.mainloop()
        # default loop contents:
        # while True:
        #    root.update_idletasks()
        #    root.update()


if __name__ == "__main__":
    main(sys.argv)
