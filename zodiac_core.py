import json
import math
import re
import sys
from os.path import isfile
from tkinter import *
from tkinter.font import Font

VERSION = "v1.1.2"

# TODO: incorporate mirror-mode/mod (hw-only), clear galaxy, nice-to-have: show other parts of galaxy as read-only (different bg color), ensure place-and-delete works fine
# TODO: system colors influence planet generation changes
# TODO: config file (ui-settings, color-settings, default settings, ...)
# TODO: warning if galaxy setting is wrong (compare with get_game)
# TODO: toggle(s) for crosshair

# TODO: incorporate SHOWRION, LOWER_C? (system-content-mirroring?)
# TODO: nebula markers?
# TODO: random populate button(s)?
# TODO: zoom-buttons? (scale-factor)
# TODO: shift everything with arrowkeys?
# ...

# LOGIC
EPSILON = 0.00001
MINIMAL_SYSTEM_SEPARATION_DISTANCE = 10
SCALE_FACTOR = .7

# GUI
SYSTEM_DRAWING_RADIUS = 8
STAR_COLOR_RADIUS = 3
WORMHOLE_SOURCE_CIRCLE_RADIUS = 10
GUI_BACKGROUND_COLOR = 'blue4'
GUI_FOREGROUND_COLOR = 'cornflowerblue'
GUI_FONT_ON_BACKGROUND_COLOR = 'white'
GALAXY_COLOR = '#161616'
CROSSHAIR_COLOR = '#505050'
GRID_COLOR = '#404080'
SYSTEM_OUTLINE_COLOR = '#454545'
NORMAL_SYSTEM_COLOR = 'black'
HOMEWORLD_COLOR = 'greenyellow'
ORION_COLOR = 'green'
BLACK_HOLE_COLOR = 'purple'
WORMHOLE_COLOR = 'darkslateblue'
RANDOM_STAR_COLOR = 'grey'
BLUE_STAR_COLOR = 'blue'
WHITE_STAR_COLOR = 'white'
YELLOW_STAR_COLOR = 'yellow'
ORANGE_STAR_COLOR = 'orange'
RED_STAR_COLOR = 'red'
BROWN_STAR_COLOR = 'brown'
INDICATOR_COLORS = {}
# INDICATOR_COLORS['4'] = 'darkorange'
# INDICATOR_COLORS['6'] = 'darkorange1'
# INDICATOR_COLORS['9'] = 'darkorange2'
# INDICATOR_COLORS['12'] = 'darkorange3'
# INDICATOR_COLORS['14'] = 'darkorange4'
# INDICATOR_COLORS['18'] = 'firebrick4'
INDICATOR_NAMES = {}
INDICATOR_NAMES['4'] = 'Standard Fuel Cells'
INDICATOR_NAMES['6'] = 'Deut. / Std.+Ext.Tank'
INDICATOR_NAMES['9'] = 'Irid. / Deut.+Ext.Tank'
INDICATOR_NAMES['12'] = '12 Parsecs: Uridium'
INDICATOR_NAMES['14'] = '14 Parsecs: Irid.+Ext.Tank'
INDICATOR_NAMES['18'] = '18 Parsecs: Urid.+Ext.Tank'

HIGHEST_PARSEC_INDICATOR_RANGE = 18

# FILE HANDLING
TEMPLATE_DRAWN_SYSTEMS_MARKER = '#DRAWN_SYSTEMS_MARKER#'
TEMPLATE_SAVESLOT_MARKER = '#SAVESLOT_MARKER#'
TITLE_MARKER = '#TITLE_MARKER#'
GALAXY_SIZE_MARKER = '#GALAXY_SIZE_MARKER#'
VERSION_MARKER = '#VERSION_MARKER#'
GALAXY_SIZE_ABBREVIATION_MARKER = '#GALAXY_SIZE_ABBREVIATION_MARKER#'

# ENCODINGS / NAMES
NORMAL_SYSTEM = 'Normal System'
HOMEWORLD = 'Homeworld'
ORION = 'Orion'
BLACK_HOLE = 'Black Hole'
RANDOM_STAR = 'Random'
BLUE_STAR = 'Blue'
WHITE_STAR = 'White'
YELLOW_STAR = 'Yellow'
ORANGE_STAR = 'Orange'
RED_STAR = 'Red'
BROWN_STAR = 'Brown'
GALAXY_SMALL = 'Small Galaxy'
GALAXY_MEDIUM = 'Medium Galaxy'
GALAXY_LARGE = 'Large Galaxy'
GALAXY_CLUSTER = 'Cluster Galaxy'
GALAXY_LARGE_HUGE_LEGACY = 'Large / Cluster Galaxy'
GALAXY_HUGE = 'Huge Galaxy'
SET_WORMHOLE = 'Set Wormhole'
CLEAR_WORMHOLE = 'Remove Wormhole'
MODE_PLACE_WORMHOLE_A = 'whA'
MODE_PLACE_WORMHOLE_B = 'whB'
SYSTEMS_REMAINING = 'Systems Remaining:'
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
    def __init__(self, size_description, width, height, nr_systems, radio_button_id):
        self.size_description = size_description
        self.width = width
        self.height = height
        self.nr_systems = nr_systems
        self.radio_button_id = radio_button_id

    def getCanvasResolution(self):
        return self.width * SCALE_FACTOR, self.height * SCALE_FACTOR

    def getCenterCanvasCoordinates(self):
        x, y = self.getCanvasResolution()
        return x / 2., y / 2.


class System:
    def __init__(self, x, y, systemType, starColor, drawnSystem, drawnStar):
        self.x = x / SCALE_FACTOR
        self.y = y / SCALE_FACTOR
        self.canvas_x = x
        self.canvas_y = y
        self.systemType = systemType
        self.starColor = starColor
        self.drawnSystem = drawnSystem
        self.drawnStar = drawnStar
        self.wormhole_partner = None
        self.wormhole = None
        self.wormholeMarker = None

    def changeSystemType(self, canvas, systemType):
        self.systemType = systemType
        if systemType.name == BLACK_HOLE:
            self.changeStarColor(canvas, BLACK_HOLE_COLOR)
        canvas.itemconfig(self.drawnSystem, fill=systemType.draw_color)

    def changeStarColor(self, canvas, starColor):
        self.starColor = starColor
        if self.systemType.name == BLACK_HOLE:
            starFillColor = BLACK_HOLE_COLOR
        else:
            starFillColor = starColor.draw_color
        canvas.itemconfig(self.drawnStar, fill=starFillColor)

    def delete(self, canvas):
        canvas.delete(self.drawnSystem)
        canvas.delete(self.drawnStar)
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
        return f'{self.systemType.name}, {self.x}, {self.y}, {self.wormhole}'


class SystemType:
    def __init__(self, name, draw_color, radio_button_id):
        self.name = name
        self.draw_color = draw_color
        self.radio_button_id = radio_button_id


class StarColor:
    def __init__(self, name, draw_color, radio_button_id):
        self.name = name
        self.draw_color = draw_color
        self.radio_button_id = radio_button_id


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
    def __init__(self, systemType, starColor, galaxy, systemClickmode, galaxy_radio, parsec_indicator_toggles,
                 mirror_mode, gridEnabled, gridResolutionInCoordinates, system_type_radio, system_color_radio):
        self.systemType = systemType
        self.starColor = starColor
        self.galaxy = galaxy
        self.systemClickmode = systemClickmode
        self.galaxy_radio = galaxy_radio
        self.blockOneClick = False
        self.parsec_indicator_toggles = parsec_indicator_toggles
        self.mirror_mode = mirror_mode
        self.gridEnabled = gridEnabled
        self.gridResolutionInCoordinates = gridResolutionInCoordinates
        self.system_type_radio = system_type_radio
        self.system_color_radio = system_color_radio

    def setSystemType(self, allSystems, canvas, systemType):
        if 'source' in self.systemClickmode.currentArguments:
            self.systemClickmode.currentArguments['source'].changeSystemType(canvas, systemType)
            update_stats(allSystems, self)
        self.systemType = systemType
        self.system_type_radio.set(systemType.radio_button_id)

    def setStarColor(self, allSystems, canvas, starColor):
        if 'source' in self.systemClickmode.currentArguments:
            self.systemClickmode.currentArguments['source'].changeStarColor(canvas, starColor)
            update_stats(allSystems, self)
        self.starColor = starColor
        self.system_color_radio.set(starColor.radio_button_id)

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
GALAXIES[GALAXY_CLUSTER] = Galaxy(GALAXY_CLUSTER, 1012, 800, 71, 3)
GALAXIES[GALAXY_HUGE] = Galaxy(GALAXY_HUGE, 1518, 1200, 71, 4)
SYSTEM_TYPES = {}
SYSTEM_TYPES[NORMAL_SYSTEM] = SystemType(NORMAL_SYSTEM, NORMAL_SYSTEM_COLOR, 0)
SYSTEM_TYPES[HOMEWORLD] = SystemType(HOMEWORLD, HOMEWORLD_COLOR, 1)
SYSTEM_TYPES[ORION] = SystemType(ORION, ORION_COLOR, 2)
SYSTEM_TYPES[BLACK_HOLE] = SystemType(BLACK_HOLE, BLACK_HOLE_COLOR, 3)
STAR_COLORS = {}
STAR_COLORS[RANDOM_STAR] = StarColor(RANDOM_STAR, RANDOM_STAR_COLOR, 0)
STAR_COLORS[BLUE_STAR] = StarColor(BLUE_STAR, BLUE_STAR_COLOR, 1)
STAR_COLORS[WHITE_STAR] = StarColor(WHITE_STAR, WHITE_STAR_COLOR, 2)
STAR_COLORS[YELLOW_STAR] = StarColor(YELLOW_STAR, YELLOW_STAR_COLOR, 3)
STAR_COLORS[ORANGE_STAR] = StarColor(ORANGE_STAR, ORANGE_STAR_COLOR, 4)
STAR_COLORS[RED_STAR] = StarColor(RED_STAR, RED_STAR_COLOR, 5)
STAR_COLORS[BROWN_STAR] = StarColor(BROWN_STAR, BROWN_STAR_COLOR, 6)


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
        g = (6. - 2. * dx) * f + dx
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
        # hex_channel_color = hex(round(15 * (17 - radius_in_parsec)))[2:]
        color = f'#{R_hex}{G_hex}{B_hex}'
    return color, contrasting_font_color


def refresh_marker_layer_order(canvas):
    for layer_behind_new_object in range(1, HIGHEST_PARSEC_INDICATOR_RANGE + 1):
        try:
            canvas.tag_lower(f'parsec_indicator_{layer_behind_new_object}', f'parsec_indicator')
        except:
            pass


def clear_galaxy(canvas, allSystems, settings):
    for system in allSystems:
        system.delete(canvas)
    allSystems.clear()
    settings.setSystemClickmode(SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A])
    update_stats(allSystems, settings)


def remove_system(canvas, system, allSystems, settings):
    system.delete(canvas)
    allSystems.remove(system)
    settings.setSystemClickmode(SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A])
    update_stats(allSystems, settings)


def change_galaxy_size(canvas, settings, galaxy, allSystems, crosshair, allGridLines):
    settings.setGalaxy(galaxy)
    canvas_width, canvas_height = galaxy.getCanvasResolution()
    canvas.config(width=canvas_width, height=canvas_height)
    clear_galaxy(canvas, allSystems, settings)
    settings.setSystemClickmode(SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A])
    center_x, center_y = galaxy.getCenterCanvasCoordinates()
    canvas.coords(crosshair['vertical'], center_x, 0, center_x, canvas_height)
    canvas.coords(crosshair['horizontal'], 0, center_y, canvas_width, center_y)
    canvas.coords(crosshair['slash'], center_x - center_y, canvas_height, center_x + center_y, 0)
    canvas.coords(crosshair['backslash'], center_x - center_y, 0, center_x + center_y, canvas_height)
    set_grid(settings, canvas, allGridLines)


def create_wormhole(source, target, canvas, allSystems, settings):
    canvas_line = canvas.create_line(source.canvas_x, source.canvas_y, target.canvas_x, target.canvas_y,
                                     fill=WORMHOLE_COLOR, width=3)
    canvas.tag_lower(canvas_line)
    try:
        canvas.tag_raise(canvas_line, f'parsec_indicator')
    except:
        pass
    try:
        canvas.tag_raise(canvas_line, f'helper_line')
    except:
        pass
    source.dissolve_wormhole()
    target.dissolve_wormhole()
    Wormhole(source, target, canvas_line, canvas)
    update_stats(allSystems, settings)


def clearSelection(settings):
    settings.systemClickmode.currentArguments['source'] = None
    settings.setSystemClickmode(SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A])


def leftclick_system(canvas, system, settings, allSystems):
    settings.blockOneClick = True
    if settings.systemClickmode.mode == MODE_PLACE_WORMHOLE_A:
        settings.setSystemClickmode(SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_B])
        source_marker = canvas.create_oval(system.canvas_x - WORMHOLE_SOURCE_CIRCLE_RADIUS,
                                           system.canvas_y - WORMHOLE_SOURCE_CIRCLE_RADIUS,
                                           system.canvas_x + WORMHOLE_SOURCE_CIRCLE_RADIUS,
                                           system.canvas_y + WORMHOLE_SOURCE_CIRCLE_RADIUS,
                                           outline=WORMHOLE_COLOR, width=3)
        canvas.tag_lower(source_marker)
        try:
            canvas.tag_raise(source_marker, f'parsec_indicator')
        except:
            pass
        try:
            canvas.tag_raise(source_marker, f'helper_line')
        except:
            pass
        settings.systemClickmode.currentArguments['source'] = system
        settings.systemClickmode.canvasMarkers.append(source_marker)
        system.wormholeMarker = source_marker
        settings.setSystemType(allSystems, canvas, system.systemType)
        settings.setStarColor(allSystems, canvas, system.starColor)
    elif settings.systemClickmode.mode == MODE_PLACE_WORMHOLE_B:
        source = settings.systemClickmode.currentArguments['source']
        print('Wormhole from ' + str(source) + " to " + str(system))
        clearSelection(settings)
        # TODO: prevent orion-wormholes? TODO: try out what happens if wormholes to blackholes are allowed!
        if source != system and source.systemType != SYSTEM_TYPES[BLACK_HOLE] and system.systemType != SYSTEM_TYPES[
            BLACK_HOLE]:
            create_wormhole(source, system, canvas, allSystems, settings)
        else:
            print('Ignoring wormhole attempt: source and target are identical')


def add_single_system(x, y, canvas, allSystems, settings):
    x = float(x)
    y = float(y)
    systemType = settings.systemType
    starColor = settings.starColor
    if systemType.name == BLACK_HOLE:
        starFillColor = BLACK_HOLE_COLOR
    else:
        starFillColor = starColor.draw_color
    polygon_points = [x - SYSTEM_DRAWING_RADIUS, y,
                      x, y - SYSTEM_DRAWING_RADIUS,
                      x + SYSTEM_DRAWING_RADIUS, y,
                      x, y + SYSTEM_DRAWING_RADIUS]
    drawnStar = canvas.create_polygon(polygon_points, fill=starFillColor, outline=SYSTEM_OUTLINE_COLOR)
    drawnSystem = canvas.create_oval(x - STAR_COLOR_RADIUS, y - STAR_COLOR_RADIUS,
                                     x + STAR_COLOR_RADIUS, y + STAR_COLOR_RADIUS,
                                     fill=systemType.draw_color, outline=SYSTEM_OUTLINE_COLOR)
    # drawnSystem = canvas.create_rectangle((event.x - STAR_RECT_RADIUS, event.y - STAR_RECT_RADIUS),
    #                                     (event.x + STAR_RECT_RADIUS, event.y + STAR_RECT_RADIUS),
    #                                     fill=systemType.draw_color)
    system = System(x, y, systemType, starColor, drawnSystem, drawnStar)
    allSystems.append(system)
    refresh_marker_layer_order(canvas)
    canvas.tag_bind(drawnSystem, '<Button-1>',
                    lambda system_left_clicked: leftclick_system(canvas, system, settings, allSystems))
    canvas.tag_bind(drawnSystem, '<Button-3>', lambda delete_event: remove_system(canvas, system, allSystems, settings))
    canvas.tag_bind(drawnStar, '<Button-1>',
                    lambda system_left_clicked: leftclick_system(canvas, system, settings, allSystems))
    canvas.tag_bind(drawnStar, '<Button-3>', lambda delete_event: remove_system(canvas, system, allSystems, settings))


def get_mirror_slashed_coordinates(systemToAdd, width, height):
    # project onto the diagonal from top left to bottom right
    projected_x = height / 4. + width / 4. - systemToAdd[1] / 2. + systemToAdd[0] / 2.

    mirrored_x = 2 * projected_x - systemToAdd[0]
    mirrored_y = systemToAdd[1] + 2 * (projected_x - systemToAdd[0])
    return (mirrored_x, mirrored_y)


def get_mirror_backslashed_coordinates(systemToAdd, width, height):
    # project onto the diagonal from bottom left to top right
    projected_x = - height / 4. + width / 4. + systemToAdd[1] / 2. + systemToAdd[0] / 2.

    mirrored_x = 2 * projected_x - systemToAdd[0]
    mirrored_y = systemToAdd[1] - 2 * (projected_x - systemToAdd[0])
    return (mirrored_x, mirrored_y)


def add_system(event, canvas, allSystems, settings):
    mirror_horizontally = settings.mirror_mode['horizontal'].get()
    mirror_vertically = settings.mirror_mode['vertical'].get()
    mirror_slash = settings.mirror_mode['slash'].get()
    mirror_backslash = settings.mirror_mode['backslash'].get()
    mirror_center = settings.mirror_mode['center'].get()
    mirror_at_system = settings.mirror_mode['system'].get()
    if settings.blockOneClick:
        settings.blockOneClick = False
        return
    if settings.gridEnabled.get():
        x, y = snap_canvas_coordinates_to_grid(float(event.x), float(event.y), settings)
    else:
        x, y = float(event.x), float(event.y)
    print(
        f'adding star at {x}, {y} (with offset: {x - settings.galaxy.getCenterCanvasCoordinates()[0]}, {y - settings.galaxy.getCenterCanvasCoordinates()[1]})')
    systemsToAdd = [(x, y)]
    width, height = settings.galaxy.getCanvasResolution()
    if mirror_at_system and 'source' in settings.systemClickmode.currentArguments:
        system_to_mirror_at = settings.systemClickmode.currentArguments['source']
        systemsToAdd.append((x + 2. * (system_to_mirror_at.canvas_x - x), y + 2. * (system_to_mirror_at.canvas_y - y)))
    if mirror_horizontally:
        newSystemToAdd = []
        for systemToAdd in systemsToAdd:
            newSystemToAdd.append(((width - systemToAdd[0], systemToAdd[1])))
        systemsToAdd.extend(newSystemToAdd)
    if mirror_vertically:
        newSystemToAdd = []
        for systemToAdd in systemsToAdd:
            newSystemToAdd.append((systemToAdd[0], height - systemToAdd[1]))
        systemsToAdd.extend(newSystemToAdd)
    if mirror_slash:
        newSystemToAdd = []
        for systemToAdd in systemsToAdd:
            newSystemToAdd.append(
                get_mirror_slashed_coordinates(systemToAdd, width, height))
        systemsToAdd.extend(newSystemToAdd)
    if mirror_backslash:
        newSystemToAdd = []
        for systemToAdd in systemsToAdd:
            newSystemToAdd.append(
                get_mirror_backslashed_coordinates(systemToAdd, width, height))
        systemsToAdd.extend(newSystemToAdd)
    if mirror_center:
        newSystemToAdd = []
        for systemToAdd in systemsToAdd:
            newSystemToAdd.append((width - systemToAdd[0], height - systemToAdd[1]))
        systemsToAdd.extend(newSystemToAdd)
    validSystems = []
    for systemToAdd in systemsToAdd:
        if systemToAdd[0] >= 0 and systemToAdd[0] <= width \
                and systemToAdd[1] >= 0 and systemToAdd[1] <= height:
            stillValid = True
            for system in allSystems:
                if math.dist([system.canvas_x, system.canvas_y],
                             [systemToAdd[0], systemToAdd[1]]) < MINIMAL_SYSTEM_SEPARATION_DISTANCE:
                    stillValid = False
                    break
            for newSystem in validSystems:
                if math.dist([newSystem[0], newSystem[1]],
                             [systemToAdd[0], systemToAdd[1]]) < MINIMAL_SYSTEM_SEPARATION_DISTANCE:
                    stillValid = False
                    break
            if stillValid == True:
                validSystems.append(systemToAdd)
            else:
                print(
                    f'Refusing to place system at x={systemToAdd[0]}, y={systemToAdd[1]}, too close to another system')

        else:
            print(f'Refusing to place system at x={systemToAdd[0]}, y={systemToAdd[1]}, out of bounds after mirroring')

    if len(validSystems) + len(allSystems) > settings.galaxy.nr_systems:
        print(f'Trying to exceed maximum number of systems for given galaxy size: {settings.galaxy.nr_systems}')
        return
    for valid_system_to_add in validSystems:
        add_single_system(valid_system_to_add[0], valid_system_to_add[1], canvas, allSystems, settings)
    update_stats(allSystems, settings)


def format_system_output(all_systems):
    output = ''
    for system in all_systems:
        if system.wormhole_partner is not None:
            output += f'{{system_type=\'{system.systemType.name}\', star_color=\'{system.starColor.name}\', x={round(system.x)}, y={round(system.y)}, wormhole_partner_x={round(system.wormhole_partner.x)}, wormhole_partner_y={round(system.wormhole_partner.y)}}}, '
        else:
            output += f'{{system_type=\'{system.systemType.name}\', star_color=\'{system.starColor.name}\', x={round(system.x)}, y={round(system.y)}}}, '
    output = output[:-2]
    print(output)
    return output


def export_map(allSystems, titleEntry, saveSlot, galaxy, loadButton):
    nrSystems = len(allSystems)
    title = titleEntry.get()
    galaxy_size = galaxy.size_description
    galaxy_size_abbreviation = galaxy_size[0]
    print(f'Exporting {nrSystems} systems for slot {saveSlot}...')
    saveslot_output = f'{saveSlot}'
    system_output = format_system_output(allSystems)
    with open('ZODIAC_TEMPLATE.CFG', 'r') as template_file:
        with open(f'ZODIAC{saveSlot}.CFG', 'w') as file_to_save:
            for line in template_file:
                if TEMPLATE_SAVESLOT_MARKER in line:
                    line = line.replace(TEMPLATE_SAVESLOT_MARKER, saveslot_output)
                if TITLE_MARKER in line:
                    line = line.replace(TITLE_MARKER, title)
                if VERSION_MARKER in line:
                    line = line.replace(VERSION_MARKER, VERSION)
                if GALAXY_SIZE_ABBREVIATION_MARKER in line:
                    line = line.replace(GALAXY_SIZE_ABBREVIATION_MARKER, galaxy_size_abbreviation)
                file_to_save.write(line)
    with open('ZODIAC_TEMPLATE.LUA', 'r') as template_file:
        with open(f'ZODIAC{saveSlot}.LUA', 'w') as file_to_save:
            for line in template_file:
                if TEMPLATE_DRAWN_SYSTEMS_MARKER in line:
                    line = line.replace(TEMPLATE_DRAWN_SYSTEMS_MARKER, system_output)
                if TITLE_MARKER in line:
                    line = line.replace(TITLE_MARKER, title)
                if GALAXY_SIZE_MARKER in line:
                    line = line.replace(GALAXY_SIZE_MARKER, galaxy_size)
                if VERSION_MARKER in line:
                    line = line.replace(VERSION_MARKER, VERSION)
                file_to_save.write(line)
    loadButton.config(state=NORMAL)
    loadButton.select()


def load_robustly_as_json(raw_string, version_float):
    print(f'Parsing {raw_string} with version {version_float}')
    return json.loads(raw_string.replace('\'', '\"').replace('=', '\":').replace(', ', ', \"').replace('{', '{\"'))


def import_map(allSystems, title_entry, save_slot, settings, canvas, crosshair, allGridLines):
    galaxy_size_line = None
    title_line = None
    systems_line = None
    version_line = None
    originalSystemType = settings.systemType
    originalStarColor = settings.starColor
    originalGridToggle = settings.gridEnabled.get()
    settings.gridEnabled.set(False)
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
            elif 'VERSION=' in line:
                version_line = line
            elif 'system_type=' in line or 'star_type=' in line:
                systems_line = line
            if galaxy_size_line is not None and title_line is not None and systems_line is not None:
                break
    loaded_galaxy_size_string = galaxy_size_line.strip().split('=')[1].strip().replace('\'', '')
    try:
        version_float = float(version_line.strip().split('=')[1].strip().replace('\'', '').replace('v', ''))
    except:
        version_float = 0.0
    loaded_title_string = title_line.strip().split('=')[1].strip().replace('\'', '')
    crude_split_systems_strings = systems_line.strip().split('}, {')
    print('Loaded values:')
    print(f'Title: \'{loaded_title_string}\'')
    print(f'Galaxy_Size: \'{loaded_galaxy_size_string}\'')
    print(f'Systems:')
    loaded_systems_strings = []
    for crude_split_system_string in crude_split_systems_strings:
        properly_split_system_string = '{' + crude_split_system_string.replace('{', '').replace('}', '') + '}'
        print(f'\'{properly_split_system_string}\'')
        loaded_systems_strings.append(properly_split_system_string)
    title_entry.delete(0, len(title_entry.get()))
    title_entry.insert(0, loaded_title_string)
    if loaded_galaxy_size_string == GALAXY_LARGE_HUGE_LEGACY:
        loaded_galaxy_size_string = GALAXY_CLUSTER
    change_galaxy_size(canvas, settings, GALAXIES[loaded_galaxy_size_string], allSystems, crosshair, allGridLines)
    for loaded_system_string in loaded_systems_strings:
        system_parameters = load_robustly_as_json(loaded_system_string, version_float)
        if 'system_type' in system_parameters:
            settings.systemType = SYSTEM_TYPES[system_parameters['system_type']]
        else:
            settings.systemType = SYSTEM_TYPES[system_parameters['star_type']]
        addSystemEvent = Event()
        addSystemEvent.x = float(system_parameters['x']) * SCALE_FACTOR
        addSystemEvent.y = float(system_parameters['y']) * SCALE_FACTOR
        if 'star_color' in system_parameters:
            settings.starColor = STAR_COLORS[system_parameters['star_color']]
        else:
            settings.starColor = STAR_COLORS[RANDOM_STAR]
        add_system(addSystemEvent, canvas, allSystems, settings)

    # ensure all systems exist before creating wormholes, still better than searching for non-existing systems
    for loaded_system_string in loaded_systems_strings:
        # system_parameters = loaded_system_string.replace('}', '').replace('{', '').split(', ')
        system_parameters = load_robustly_as_json(loaded_system_string, version_float)
        if 'wormhole_partner_x' in system_parameters and 'wormhole_partner_y' in system_parameters:
            found = False
            source_x = float(system_parameters['x'])
            source_y = float(system_parameters['y'])
            target_x = float(system_parameters['wormhole_partner_x'])
            target_y = float(system_parameters['wormhole_partner_y'])
            for source in allSystems:
                if source.wormhole_partner is None and abs(source.x - source_x) < EPSILON and abs(source.y - source_y) < EPSILON:
                    for target in allSystems:
                        if target.wormhole_partner is None and abs(target.x - target_x) < EPSILON and abs(target.y - target_y) < EPSILON:
                            found = True
                            create_wormhole(source, target, canvas, allSystems, settings)
                            break
                if found == True:
                    break
            if found == False:
                # valid, will occur once per wormhole because the partner coordinates are stored for both systems
                pass

    clearSelection(settings)
    settings.setSystemType(allSystems, canvas, originalSystemType)
    settings.setStarColor(allSystems, canvas, originalStarColor)
    settings.gridEnabled.set(originalGridToggle)


def update_stats(allSystems, settings):
    stat_labels[SYSTEMS_REMAINING].config(
        text=f'{settings.galaxy.nr_systems - len(allSystems)} / {settings.galaxy.nr_systems}')
    stat_labels[NORMALS_PLACED].config(
        text=f'{int(sum(system.systemType == SYSTEM_TYPES[NORMAL_SYSTEM] for system in allSystems))}')
    stat_labels[HOMEWORLDS_PLACED].config(
        text=f'{int(sum(system.systemType == SYSTEM_TYPES[HOMEWORLD] for system in allSystems))}')
    stat_labels[ORIONS_PLACED].config(
        text=f'{int(sum(system.systemType == SYSTEM_TYPES[ORION] for system in allSystems))}')
    stat_labels[BLACK_HOLES_PLACED].config(
        text=f'{int(sum(system.systemType == SYSTEM_TYPES[BLACK_HOLE] for system in allSystems))}')
    stat_labels[WORMHOLES_PLACED].config(
        text=f'{int(sum(system.wormhole_partner is not None for system in allSystems) / 2)}')


def change_parsec_indicator(canvas, parsecIndicators, radius_in_parsec, parsec_indicator_toggles):
    if parsec_indicator_toggles[str(radius_in_parsec)].get():
        enable_parsec_indicator(canvas, parsecIndicators, radius_in_parsec)
    else:
        disable_parsec_indicator(canvas, parsecIndicators, radius_in_parsec)
    refresh_marker_layer_order(canvas)


def parsecs_to_canvas_distance(parsecs):
    return parsecs2distance(parsecs) * SCALE_FACTOR


def enable_parsec_indicator(canvas, parsecIndicators, radius_in_parsec):
    radius_in_scaled_coordinates = parsecs_to_canvas_distance(radius_in_parsec)
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


def parsecs2distance(parsecs):
    # true value seems to be 30 but avoid not being in range due to rounding errors;
    # 0.6 will theoretically become noticable accross 50 horizontal parsec in huge galaxy
    return parsecs * 29.5


def validate_grid_resolution(string):
    # taken and adjusted from https://stackoverflow.com/questions/46116037/tkinter-restrict-entry-data-to-float
    if string == '':
        return True
    regex = re.compile(r"[0-9.]*$")
    result = regex.match(string)
    try:
        float(result.group())
        return True
    except:
        return False


# TODO: is probably a redundant method
def check_grid_resolution_entry(P):
    return validate_grid_resolution(P)


def on_grid_resolution_changed(newValue, settings, canvas, allGridLines):
    newValueAsStr = newValue.get()
    settings.gridResolutionInCoordinates = 0. if newValueAsStr == '' else parsecs_to_canvas_distance(
        float(newValueAsStr))
    set_grid(settings, canvas, allGridLines)


def set_grid(settings, canvas, allGridLines):
    for gridLine in allGridLines:
        canvas.delete(gridLine)
    allGridLines.clear()
    if settings.gridResolutionInCoordinates > 0.:
        draw_grid(settings, canvas, allGridLines)


def create_grid_line(x1, y1, x2, y2, allGridLines, canvas):
    newLine = canvas.create_line(x1, y1, x2, y2, fill=GRID_COLOR, width=1, tags=('helper_line'))
    canvas.tag_lower(newLine)
    try:
        canvas.tag_raise(newLine, f'parsec_indicator')
    except:
        pass
    allGridLines.append(newLine)


def draw_grid(settings, canvas, allGridLines):
    canvasWidth, canvasHeight = settings.galaxy.getCanvasResolution()
    centerX, centerY = settings.galaxy.getCenterCanvasCoordinates()
    canvasStep = settings.gridResolutionInCoordinates

    create_grid_line(0, centerY, canvasWidth, centerY, allGridLines, canvas)
    create_grid_line(centerX, 0, centerX, canvasHeight, allGridLines, canvas)

    nextOffset = 0
    while nextOffset < centerX:
        nextOffset += canvasStep
        nextNorth = centerY - nextOffset
        nextSouth = centerY + nextOffset
        nextWest = centerX - nextOffset
        nextEast = centerX + nextOffset
        create_grid_line(0, nextNorth, canvasWidth, nextNorth, allGridLines, canvas)
        create_grid_line(0, nextSouth, canvasWidth, nextSouth, allGridLines, canvas)
        create_grid_line(nextWest, 0, nextWest, canvasHeight, allGridLines, canvas)
        create_grid_line(nextEast, 0, nextEast, canvasHeight, allGridLines, canvas)


def snap_canvas_coordinates_to_grid(x, y, settings):
    centerX, centerY = settings.galaxy.getCenterCanvasCoordinates()
    canvasStepSize = settings.gridResolutionInCoordinates
    snappedX = round((x - centerX) / canvasStepSize) * canvasStepSize + centerX
    snappedY = round((y - centerY) / canvasStepSize) * canvasStepSize + centerY
    # print(f'stepsize {canvasStepSize}')
    return snappedX, snappedY


def main(argv):
    root = Tk()
    root.title(f'Zodiac {VERSION} (by Epirasque -> https://discord.gg/45BnvY4 or romanhable@web.de)')
    root.configure(background=GUI_BACKGROUND_COLOR)

    button_window = Frame(root)
    button_window.configure(background=GUI_BACKGROUND_COLOR)
    button_window.grid(row=0, column=0, sticky='nwse')

    canvas_width = GALAXIES[GALAXY_HUGE].width * SCALE_FACTOR
    canvas_height = GALAXIES[GALAXY_HUGE].height * SCALE_FACTOR

    canvas_frame = Frame(root)
    canvas_frame.configure(background=GUI_BACKGROUND_COLOR)
    canvas_frame.grid(row=0, column=1, sticky="nswe")

    canvas_header_frame = Frame(canvas_frame)
    canvas_header_frame.configure(background=GUI_BACKGROUND_COLOR)
    canvas_header_frame.grid(row=0, column=0, sticky="nswe")

    # TODO: consider highlightthickness=0
    canvas = Canvas(canvas_frame, width=canvas_width, height=canvas_height, bg=GALAXY_COLOR,
                    highlightbackground=GUI_FOREGROUND_COLOR)
    SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A] = SystemClickmode(MODE_PLACE_WORMHOLE_A, canvas)
    SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_B] = SystemClickmode(MODE_PLACE_WORMHOLE_B, canvas)

    app_width = round(canvas_width + 530)
    app_height = round(canvas_height + 140)

    root.geometry(f'{app_width}x{app_height}+50+10')
    root.resizable(True, True)

    allSystems = []
    allGridLines = []
    parsec_indicator_toggles = {}

    crosshair_vertical = canvas.create_line(canvas_width / 2, 0, canvas_width / 2, canvas_height,
                                            fill=CROSSHAIR_COLOR, width=3, tags=('helper_line'))
    crosshair_horizontal = canvas.create_line(0, canvas_height / 2, canvas_width, canvas_height / 2,
                                              fill=CROSSHAIR_COLOR, width=3, tags=('helper_line'))
    crosshair_slash = canvas.create_line(- canvas_height / 2 + canvas_width / 2, canvas_height,
                                         canvas_height / 2 + canvas_width / 2, 0,
                                         fill=CROSSHAIR_COLOR, width=3, tags=('helper_line'))
    crosshair_backslash = canvas.create_line(- canvas_height / 2 + canvas_width / 2, 0,
                                             canvas_height / 2 + canvas_width / 2, canvas_height,
                                             fill=CROSSHAIR_COLOR, width=3, tags=('helper_line'))
    crosshair = {'vertical': crosshair_vertical, 'horizontal': crosshair_horizontal,
                 'slash': crosshair_slash, 'backslash': crosshair_backslash}
    # center = canvas.create_oval((canvas_width / 2) - 3, (canvas_height / 2) - 3, (canvas_width / 2) + 3,
    #                            (canvas_height / 2) + 3, fill=ORION_COLOR)
    canvas.coords(crosshair['vertical'], canvas_width / 2, 0, canvas_width / 2, canvas_height)
    canvas.coords(crosshair['horizontal'], 0, canvas_height / 2, canvas_width, canvas_height / 2)
    canvas.coords(crosshair['slash'], - canvas_height / 2 + canvas_width / 2, canvas_height,
                  canvas_height / 2 + canvas_width / 2, 0)
    canvas.coords(crosshair['backslash'], - canvas_height / 2 + canvas_width / 2, 0,
                  canvas_height / 2 + canvas_width / 2, canvas_height)

    # TODO: consider: , bd=0) \
    Label(button_window, text='GALAXY SIZE', relief=GROOVE, bg=GUI_FOREGROUND_COLOR) \
        .grid(row=0, column=0, padx=5, pady=5)
    galaxy_radio = IntVar()
    galaxy_radio.set(4)

    mirror_horizontally = BooleanVar()
    mirror_vertically = BooleanVar()
    mirror_slash = BooleanVar()
    mirror_backslash = BooleanVar()
    mirror_center = BooleanVar()
    mirror_at_system = BooleanVar()
    mirror_mode = {'horizontal': mirror_horizontally, 'vertical': mirror_vertically, 'slash': mirror_slash,
                   'backslash': mirror_backslash, 'center': mirror_center, 'system': mirror_at_system}
    snap_to_grid = BooleanVar()
    snap_to_grid.set(False)
    system_type_radio = IntVar()
    system_type_radio.set(0)
    star_color_radio = IntVar()
    star_color_radio.set(0)
    settings = Settings(SYSTEM_TYPES[NORMAL_SYSTEM], STAR_COLORS[RANDOM_STAR], GALAXIES[GALAXY_HUGE],
                        SYSTEM_CLICK_MODES[MODE_PLACE_WORMHOLE_A],
                        galaxy_radio, parsec_indicator_toggles, mirror_mode, snap_to_grid, 4.0,
                        system_type_radio, star_color_radio)

    Radiobutton(button_window, text=GALAXY_SMALL, indicatoron=False, variable=galaxy_radio, value=0,
                activebackground=GALAXY_COLOR, bg=GALAXY_COLOR, selectcolor=GALAXY_COLOR,
                fg='white', activeforeground='white',
                command=lambda: change_galaxy_size(canvas, settings, GALAXIES[GALAXY_SMALL], allSystems, crosshair,
                                                   allGridLines)) \
        .grid(row=1, column=0, padx=5, pady=5)
    Radiobutton(button_window, text=GALAXY_MEDIUM, indicatoron=False, variable=galaxy_radio, value=1,
                activebackground=GALAXY_COLOR, bg=GALAXY_COLOR, selectcolor=GALAXY_COLOR,
                fg='white', activeforeground='white',
                command=lambda: change_galaxy_size(canvas, settings, GALAXIES[GALAXY_MEDIUM], allSystems, crosshair,
                                                   allGridLines)) \
        .grid(row=2, column=0, padx=5, pady=5)
    Radiobutton(button_window, text=GALAXY_LARGE, indicatoron=False, variable=galaxy_radio, value=2,
                activebackground=GALAXY_COLOR, bg=GALAXY_COLOR, selectcolor=GALAXY_COLOR,
                fg='white', activeforeground='white',
                command=lambda: change_galaxy_size(canvas, settings, GALAXIES[GALAXY_LARGE], allSystems, crosshair,
                                                   allGridLines)) \
        .grid(row=3, column=0, padx=5, pady=5)
    Radiobutton(button_window, text=GALAXY_CLUSTER, indicatoron=False, variable=galaxy_radio, value=3,
                activebackground=GALAXY_COLOR, bg=GALAXY_COLOR, selectcolor=GALAXY_COLOR,
                fg='white', activeforeground='white',
                command=lambda: change_galaxy_size(canvas, settings, GALAXIES[GALAXY_CLUSTER], allSystems, crosshair,
                                                   allGridLines)) \
        .grid(row=4, column=0, padx=5, pady=5)
    Radiobutton(button_window, text=GALAXY_HUGE, indicatoron=False, variable=galaxy_radio, value=4,
                activebackground=GALAXY_COLOR, bg=GALAXY_COLOR, selectcolor=GALAXY_COLOR,
                fg='white', activeforeground='white',
                command=lambda: change_galaxy_size(canvas, settings, GALAXIES[GALAXY_HUGE], allSystems, crosshair,
                                                   allGridLines)) \
        .grid(row=5, column=0, padx=5, pady=5)

    grid_resolution_frame = Frame(button_window)
    grid_resolution_frame.configure(background=GUI_BACKGROUND_COLOR)
    grid_resolution_frame.grid(row=1, column=1, sticky='nwse')

    Label(button_window, text='GRID SETTINGS', relief=GROOVE, bg=GUI_FOREGROUND_COLOR) \
        .grid(row=0, column=1, padx=5, pady=5)
    Label(grid_resolution_frame, text='Grid-Size In Parsec', bg=GUI_BACKGROUND_COLOR, fg=GUI_FONT_ON_BACKGROUND_COLOR) \
        .grid(row=0, column=0, sticky=W, padx=5, pady=5)
    grid_resolution_entry_value = StringVar()
    grid_resolution_entry_value.trace("w",
                                      lambda name, index, mode, grid_resolution_entry_value=grid_resolution_entry_value: \
                                          on_grid_resolution_changed(grid_resolution_entry_value, settings, canvas,
                                                                     allGridLines))
    grid_resolution_entry = Entry(grid_resolution_frame, width=5, validate="key",
                                  textvariable=grid_resolution_entry_value)
    grid_resolution_entry.grid(row=0, column=1, sticky=E, padx=1, pady=5)
    grid_resolution_entry.insert(0, '4.0')
    grid_resolution_command = (grid_resolution_entry.register(check_grid_resolution_entry), '%P')
    grid_resolution_entry.config(validatecommand=grid_resolution_command)

    Checkbutton(button_window, text='Snap To Grid', indicatoron=False, variable=snap_to_grid,
                activebackground=GRID_COLOR, bg=GRID_COLOR, selectcolor=GRID_COLOR,
                fg='white', activeforeground='white') \
        .grid(row=2, column=1, padx=5, pady=5)

    Label(button_window, text='PLACEMENT TYPE', relief=GROOVE, background=GUI_FOREGROUND_COLOR) \
        .grid(row=6, column=0, padx=5, pady=5)

    Radiobutton(button_window, text=HOMEWORLD, indicatoron=False, variable=system_type_radio, value=1,
                activebackground=HOMEWORLD_COLOR, bg=HOMEWORLD_COLOR, selectcolor=HOMEWORLD_COLOR,
                command=lambda: settings.setSystemType(allSystems, canvas, SYSTEM_TYPES[HOMEWORLD])) \
        .grid(row=8, column=0, padx=5, pady=5)
    Radiobutton(button_window, text=NORMAL_SYSTEM, indicatoron=False, variable=system_type_radio, value=0,
                activebackground=NORMAL_SYSTEM_COLOR, bg=NORMAL_SYSTEM_COLOR, selectcolor=NORMAL_SYSTEM_COLOR,
                fg='white', activeforeground='white',
                command=lambda: settings.setSystemType(allSystems, canvas, SYSTEM_TYPES[NORMAL_SYSTEM])) \
        .grid(row=7, column=0, padx=5, pady=5)
    Radiobutton(button_window, text=ORION, indicatoron=False, variable=system_type_radio, value=2,
                activebackground=ORION_COLOR, bg=ORION_COLOR, selectcolor=ORION_COLOR,
                fg='white', activeforeground='white',
                command=lambda: settings.setSystemType(allSystems, canvas, SYSTEM_TYPES[ORION])) \
        .grid(row=9, column=0, padx=5, pady=5)
    Radiobutton(button_window, text=BLACK_HOLE, indicatoron=False, variable=system_type_radio, value=3,
                activebackground=BLACK_HOLE_COLOR, bg=BLACK_HOLE_COLOR, selectcolor=BLACK_HOLE_COLOR,
                fg='white', activeforeground='white',
                command=lambda: settings.setSystemType(allSystems, canvas, SYSTEM_TYPES[BLACK_HOLE])) \
        .grid(row=10, column=0, padx=5, pady=5)

    Label(button_window, text='STAR COLOR (PURELY COSMETIC!)', relief=GROOVE, background=GUI_FOREGROUND_COLOR) \
        .grid(row=6, column=1, padx=5, pady=5)

    star_color_frame = Frame(button_window)
    star_color_frame.configure(background=GUI_BACKGROUND_COLOR)
    star_color_frame.grid(row=7, column=1, rowspan=5, columnspan=1, sticky='n')

    Radiobutton(star_color_frame, text=RANDOM_STAR, indicatoron=False, variable=star_color_radio, value=0,
                activebackground=RANDOM_STAR_COLOR, bg=RANDOM_STAR_COLOR, selectcolor=RANDOM_STAR_COLOR,
                command=lambda: settings.setStarColor(allSystems, canvas, STAR_COLORS[RANDOM_STAR])) \
        .grid(row=0, column=0, padx=5, pady=5, sticky='E')
    Radiobutton(star_color_frame, text=BLUE_STAR, indicatoron=False, variable=star_color_radio, value=1,
                activebackground=BLUE_STAR_COLOR, bg=BLUE_STAR_COLOR, selectcolor=BLUE_STAR_COLOR,
                fg='white', activeforeground='white',
                command=lambda: settings.setStarColor(allSystems, canvas, STAR_COLORS[BLUE_STAR])) \
        .grid(row=1, column=0, padx=5, pady=5, sticky='E')
    Radiobutton(star_color_frame, text=WHITE_STAR, indicatoron=False, variable=star_color_radio, value=2,
                activebackground=WHITE_STAR_COLOR, bg=WHITE_STAR_COLOR, selectcolor=WHITE_STAR_COLOR,
                command=lambda: settings.setStarColor(allSystems, canvas, STAR_COLORS[WHITE_STAR])) \
        .grid(row=2, column=0, padx=5, pady=5, sticky='E')
    Radiobutton(star_color_frame, text=YELLOW_STAR, indicatoron=False, variable=star_color_radio, value=3,
                activebackground=YELLOW_STAR_COLOR, bg=YELLOW_STAR_COLOR, selectcolor=YELLOW_STAR_COLOR,
                command=lambda: settings.setStarColor(allSystems, canvas, STAR_COLORS[YELLOW_STAR])) \
        .grid(row=3, column=0, padx=5, pady=5, sticky='E')
    Radiobutton(star_color_frame, text=ORANGE_STAR, indicatoron=False, variable=star_color_radio, value=4,
                activebackground=ORANGE_STAR_COLOR, bg=ORANGE_STAR_COLOR, selectcolor=ORANGE_STAR_COLOR,
                command=lambda: settings.setStarColor(allSystems, canvas, STAR_COLORS[ORANGE_STAR])) \
        .grid(row=1, column=1, padx=5, pady=5, sticky='W')
    Radiobutton(star_color_frame, text=RED_STAR, indicatoron=False, variable=star_color_radio, value=5,
                activebackground=RED_STAR_COLOR, bg=RED_STAR_COLOR, selectcolor=RED_STAR_COLOR,
                command=lambda: settings.setStarColor(allSystems, canvas, STAR_COLORS[RED_STAR])) \
        .grid(row=2, column=1, padx=5, pady=5, sticky='W')
    Radiobutton(star_color_frame, text=BROWN_STAR, indicatoron=False, variable=star_color_radio, value=6,
                activebackground=BROWN_STAR_COLOR, bg=BROWN_STAR_COLOR, selectcolor=BROWN_STAR_COLOR,
                fg='white', activeforeground='white',
                command=lambda: settings.setStarColor(allSystems, canvas, STAR_COLORS[BROWN_STAR])) \
        .grid(row=3, column=1, padx=5, pady=5, sticky='W')

    Label(button_window, text='MIRROR PLACEMENTS', relief=GROOVE, background=GUI_FOREGROUND_COLOR) \
        .grid(row=11, column=1, padx=5, pady=5)

    Checkbutton(button_window, text='Mirror Horizontally', indicatoron=False, variable=mirror_horizontally,
                activebackground='cadetblue1', bg='cadetblue1', selectcolor='cadetblue1') \
        .grid(row=12, column=0, padx=5, pady=5)

    Checkbutton(button_window, text='Mirror Vertically', indicatoron=False, variable=mirror_vertically,
                activebackground='cadetblue1', bg='cadetblue1', selectcolor='cadetblue1') \
        .grid(row=13, column=0, padx=5, pady=5)

    Checkbutton(button_window, text='Mirror /', indicatoron=False, variable=mirror_slash,
                activebackground='cadetblue1', bg='cadetblue1', selectcolor='cadetblue1') \
        .grid(row=12, column=1, padx=5, pady=5)

    Checkbutton(button_window, text='Mirror \\', indicatoron=False, variable=mirror_backslash,
                activebackground='cadetblue1', bg='cadetblue1', selectcolor='cadetblue1') \
        .grid(row=13, column=1, padx=5, pady=5)

    Checkbutton(button_window, text='Mirror at center point', indicatoron=False, variable=mirror_center,
                activebackground='cadetblue1', bg='cadetblue1', selectcolor='cadetblue1') \
        .grid(row=12, column=2, padx=5, pady=5)

    Checkbutton(button_window, text='Mirror at selected system', indicatoron=False, variable=mirror_at_system,
                activebackground='cadetblue1', bg='cadetblue1', selectcolor='cadetblue1') \
        .grid(row=13, column=2, padx=5, pady=5)

    Label(button_window, text='RANGE INDICATORS', relief=GROOVE, background=GUI_FOREGROUND_COLOR) \
        .grid(row=14, column=2, padx=5, pady=5)
    parsec_indicator_toggles['1'] = BooleanVar()  # 1 Parsec (singular) has different text
    parsecIndicators = {}
    button_color, contrasting_font_color = get_parsec_indicator_color(1)
    Checkbutton(button_window, text='1 Parsec', indicatoron=False, variable=parsec_indicator_toggles['1'],
                activebackground=button_color, bg=button_color, selectcolor=button_color,
                fg=contrasting_font_color, activeforeground=contrasting_font_color,
                command=lambda: change_parsec_indicator(canvas, parsecIndicators, 1, parsec_indicator_toggles)) \
        .grid(row=15, column=2, padx=5, pady=5)
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
            .grid(row=15 - 1 + parsec_radius, column=2, padx=5, pady=5)
    parsec_indicator_toggles['12'] = BooleanVar()
    button_color, contrasting_font_color = get_parsec_indicator_color(12)
    Checkbutton(button_window, text=INDICATOR_NAMES['12'], indicatoron=False, variable=parsec_indicator_toggles['12'],
                activebackground=button_color, bg=button_color, selectcolor=button_color,
                fg=contrasting_font_color, activeforeground=contrasting_font_color,
                command=lambda: change_parsec_indicator(canvas, parsecIndicators, 12, parsec_indicator_toggles)) \
        .grid(row=26, column=2, padx=5, pady=5)
    parsec_indicator_toggles['14'] = BooleanVar()
    button_color, contrasting_font_color = get_parsec_indicator_color(14)
    Checkbutton(button_window, text=INDICATOR_NAMES['14'], indicatoron=False, variable=parsec_indicator_toggles['14'],
                activebackground=button_color, bg=button_color, selectcolor=button_color,
                fg=contrasting_font_color, activeforeground=contrasting_font_color,
                command=lambda: change_parsec_indicator(canvas, parsecIndicators, 14, parsec_indicator_toggles)) \
        .grid(row=27, column=2, padx=5, pady=5)
    parsec_indicator_toggles['18'] = BooleanVar()
    button_color, contrasting_font_color = get_parsec_indicator_color(18)
    Checkbutton(button_window, text=INDICATOR_NAMES['18'], indicatoron=False, variable=parsec_indicator_toggles['18'],
                activebackground=button_color, bg=button_color, selectcolor=button_color,
                fg=contrasting_font_color, activeforeground=contrasting_font_color,
                command=lambda: change_parsec_indicator(canvas, parsecIndicators, 18, parsec_indicator_toggles)) \
        .grid(row=28, column=2, padx=5, pady=5)

    Label(canvas_header_frame, text='Galaxy Title', bg=GUI_BACKGROUND_COLOR, fg=GUI_FONT_ON_BACKGROUND_COLOR).grid(
        row=0, column=0, sticky=W, padx=1, pady=5)
    title_entry = Entry(canvas_header_frame, width=20)
    title_entry.grid(row=0, column=1, sticky=W, padx=1, pady=5)
    title_entry.insert(0, 'My Zodiac Galaxy')

    bold_font = Font(weight="bold")

    Label(canvas_header_frame, text=SYSTEMS_REMAINING, bg=GUI_BACKGROUND_COLOR, fg=GUI_FONT_ON_BACKGROUND_COLOR).grid(
        row=0, column=2, sticky=W, padx=1, pady=5)
    stat_labels[SYSTEMS_REMAINING] = Label(canvas_header_frame, text='??/??', font=bold_font,
                                           background=GUI_BACKGROUND_COLOR, foreground=GUI_FONT_ON_BACKGROUND_COLOR)
    stat_labels[SYSTEMS_REMAINING].grid(row=0, column=3, sticky=W, padx=1, pady=5)
    Label(canvas_header_frame, text=NORMALS_PLACED, bg=GUI_BACKGROUND_COLOR, fg=GUI_FONT_ON_BACKGROUND_COLOR).grid(
        row=0, column=4, sticky=W, padx=1, pady=5)
    stat_labels[NORMALS_PLACED] = Label(canvas_header_frame, text='?', font=bold_font, fg='white',
                                        bg=NORMAL_SYSTEM_COLOR)
    stat_labels[NORMALS_PLACED].grid(row=0, column=5, sticky=W, padx=1, pady=5)
    Label(canvas_header_frame, text=HOMEWORLDS_PLACED, bg=GUI_BACKGROUND_COLOR, fg=GUI_FONT_ON_BACKGROUND_COLOR).grid(
        row=0, column=6, sticky=W, padx=1, pady=5)
    stat_labels[HOMEWORLDS_PLACED] = Label(canvas_header_frame, text='?', font=bold_font, fg='white',
                                           bg=HOMEWORLD_COLOR)
    stat_labels[HOMEWORLDS_PLACED].grid(row=0, column=7, sticky=W, padx=1, pady=5)
    Label(canvas_header_frame, text=ORIONS_PLACED, bg=GUI_BACKGROUND_COLOR, fg=GUI_FONT_ON_BACKGROUND_COLOR).grid(row=0,
                                                                                                                  column=8,
                                                                                                                  sticky=W,
                                                                                                                  padx=1,
                                                                                                                  pady=5)
    stat_labels[ORIONS_PLACED] = Label(canvas_header_frame, text='?', font=bold_font, fg='white', bg=ORION_COLOR)
    stat_labels[ORIONS_PLACED].grid(row=0, column=9, sticky=W, padx=1, pady=5)
    Label(canvas_header_frame, text=BLACK_HOLES_PLACED, bg=GUI_BACKGROUND_COLOR, fg=GUI_FONT_ON_BACKGROUND_COLOR).grid(
        row=0, column=10, sticky=W, padx=1, pady=5)
    stat_labels[BLACK_HOLES_PLACED] = Label(canvas_header_frame, text='?', font=bold_font, fg='white',
                                            bg=BLACK_HOLE_COLOR)
    stat_labels[BLACK_HOLES_PLACED].grid(row=0, column=11, sticky=W, padx=1, pady=5)
    Label(canvas_header_frame, text=WORMHOLES_PLACED, bg=GUI_BACKGROUND_COLOR, fg=GUI_FONT_ON_BACKGROUND_COLOR).grid(
        row=0, column=12, sticky=W, padx=1, pady=5)
    stat_labels[WORMHOLES_PLACED] = Label(canvas_header_frame, text='?', font=bold_font, fg='white', bg=WORMHOLE_COLOR)
    stat_labels[WORMHOLES_PLACED].grid(row=0, column=13, sticky=W, padx=1, pady=5)

    update_stats(allSystems, settings)

    Label(button_window, text='GALAXY EXPORT', relief=GROOVE, background=GUI_FOREGROUND_COLOR) \
        .grid(row=14, column=0, padx=5, pady=5)
    Label(button_window, text='GALAXY IMPORT', relief=GROOVE, background=GUI_FOREGROUND_COLOR) \
        .grid(row=14, column=1, padx=5, pady=5)
    load_radio = IntVar()
    for save_slot in range(10):
        # save_slot=save_slot prevents the value to be evaluated/overwritten later on
        load_button = Radiobutton(button_window, text=f'Load ZODIAC{save_slot}', indicatoron=False, variable=load_radio,
                                  value=save_slot,
                                  command=lambda save_slot=save_slot: import_map(allSystems, title_entry, save_slot,
                                                                                 settings, canvas, crosshair,
                                                                                 allGridLines))
        load_button.grid(row=15 + save_slot, column=0, padx=5, pady=5)
        if not isfile(f'ZODIAC{save_slot}.LUA'):
            load_button.config(state=DISABLED)

        Button(button_window, text=f'Save ZODIAC{save_slot}',
               command=lambda save_slot=save_slot, load_button=load_button:
               export_map(allSystems, title_entry, save_slot, settings.galaxy, load_button)) \
            .grid(row=15 + save_slot, column=1, padx=5, pady=5)

    canvas.grid(row=1, column=0, sticky=NW)
    canvas.bind('<Button-1>', lambda add_event: add_system(add_event, canvas, allSystems, settings))
    canvas.bind('<Button-3>', lambda add_event: clearSelection(settings))

    def getPosition(event):
        x = canvas.winfo_pointerx() - canvas.winfo_rootx()
        y = canvas.winfo_pointery() - canvas.winfo_rooty()
        if snap_to_grid.get() == True and settings.gridResolutionInCoordinates > 0.:
            x, y = snap_canvas_coordinates_to_grid(x, y, settings)
        for radius_in_parsec, indicator in parsecIndicators.items():
            radius_in_scaled_coordinates = parsecs_to_canvas_distance(radius_in_parsec)
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
