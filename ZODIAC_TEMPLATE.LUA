--[[
	Template used when creating a hand-drawn map with the provided tool.

	Questions etc. to: https://discord.gg/45BnvY4 or romanhable@web.de (Epirasque)
]]

TITLE='#TITLE_MARKER#'
GALAXY_SIZE='#GALAXY_SIZE_MARKER#'
VERSION='#VERSION_MARKER#'

set_seed()

local drawn_systems = {
	#DRAWN_SYSTEMS_MARKER#
}

NORMAL_SYSTEM_ENCODING = 'Normal System'
HOMEWORLD_ENCODING = 'Homeworld'
ORION_ENCODING = 'Orion'
BLACK_HOLE_ENCODING = 'Black Hole'
BLACK_HOLE_COLOUR_NUMBER = 6
STAR_COLOR_NAME_TO_NUMBER = {
	Blue = 0,
	White = 1,
	Yellow = 2,
	Orange = 3,
	Red = 4,
	Brown = 5
}
ORDINARY_MONSTER_NAMES = {
	"Amoeba", "Crystal", "Dragon", "Eel", "Hydra"
}

function count_dictionary_entries(dict)
	local nr_entries = 0
	for k,v in pairs(dict) do
		nr_entries = nr_entries + 1
	end
	collectgarbage()
	return nr_entries
end

function merge_tables(table1, table2) -- arbitrary nr. of parameters using (...) with arg apparently not supported
    local result = {table.unpack(table1)}
    table.move(table2, 1, count_dictionary_entries(table2), count_dictionary_entries(result)+1, result)
    return result
end

function shuffle(table_to_shuffle)
	for i = count_dictionary_entries(table_to_shuffle), 2, -1 do
		local j = random(i)
		table_to_shuffle[i], table_to_shuffle[j] = table_to_shuffle[j], table_to_shuffle[i]
	end
end

function initialize_player_dependent_information(players, planets, stars)
	local home_systems = {}
	local nr_players = 0
    for i, player in pairs(players) do
		local home_system = stars[planets[player.home_planet].star]
		nr_players = nr_players + 1
		table.insert(home_systems, home_system)
	end
	return nr_players, home_systems
end

function get_next_valid_star_id(stars, next_system_id, home_systems)
	if next_system_id >= count_dictionary_entries(stars) then
		return -1
	end
	while next_system_id < count_dictionary_entries(stars) do
		next_system_id = next_system_id + 1
		local star = stars[next_system_id]
		if star.keep == true then
		else
			break
		end
	end
	return next_system_id
end

function galaxy_size_int_to_name(size, is_cluster)
	local string size_string = "UNKNOWN"
	if size == 0 then
		size_string = "Small"
	elseif size == 1 then
		size_string = "Medium"
	elseif size == 2 then
		size_string = "Large"
	elseif size == 3 then
		if is_cluster == 1 then
			size_string = "Cluster"
		else
			-- huge is originally encoded with same size as cluster
			size = size + 1
			size_string = "Huge"
		end
	end
	return size_string .. ' Galaxy'
end

function count_non_guardian_monsters()
	local nr_monsters = 0
	for i, s in pairs(get_ships()) do
		if s.player >= 10 and s.player <= 14 then
			nr_monsters = nr_monsters + 1
		end
	end
	collectgarbage()
	return nr_monsters
end

msgbox('Generating Zodiac Map (' .. VERSION .. ', ' .. GALAXY_SIZE .. '):\n' .. TITLE)
set_stars({}) -- early check that we're in universal context (inspired by hwmirror.lua)

shuffle(drawn_systems) --don't always use the same homeworld locations (also for the same players), same goes for possible orion locations

local nr_original_monsters = count_non_guardian_monsters()

local stars = get_stars()

local players = get_players()
local planets = get_planets()

local nr_players, home_systems = initialize_player_dependent_information(players, planets, stars)

local game = get_game()
local max_x = game.map_max_x
local max_y = game.map_max_y
local ingame_galaxy_string = galaxy_size_int_to_name(game.galaxy_size, game.is_cluster)
local nr_stars = count_dictionary_entries(stars)
local nr_original_possible_monster_locations = nr_stars
print('original systems: ' .. tostring(nr_stars))

-- TODO: support for having no orion in the game? or just don't place a marker and it will be removed, seems fine as well
local orion = stars[0]
local orion_placed = false

local planets_to_delete = {}

if ingame_galaxy_string ~= GALAXY_SIZE then
	msgbox('Zodiac ERROR: given Zodiac Galaxy was created as \'' .. GALAXY_SIZE .. '\' whereas ingame settings are set to \'' .. ingame_galaxy_string .. '\'!\nThey are supposed to be identical!')
end

for d, drawn_system in ipairs(drawn_systems) do
	if drawn_system.system_type == ORION_ENCODING and (drawn_system.placed == nil or drawn_system.placed ~= true) then
		if orion_placed == false then
			print('placing orion...')
			orion_placed = true
			orion.x = drawn_system.x
			orion.y = drawn_system.y
			orion.wormhole_partner_x = drawn_system.wormhole_partner_x
			orion.wormhole_partner_y = drawn_system.wormhole_partner_y
			orion.keep = true
			orion.is_orion = true
			drawn_system.placed = true
			nr_original_possible_monster_locations = nr_original_possible_monster_locations - 1
		else
			drawn_system.system_type = NORMAL_SYSTEM_ENCODING
		end
	end
end

collectgarbage()

print('placing homeworlds...')
for p = 1, nr_players do
	local home_system = home_systems[p]
	for j, drawn_system in ipairs(drawn_systems) do
		if drawn_system.system_type == HOMEWORLD_ENCODING and (drawn_system.placed == nil or drawn_system.placed ~= true) then
			home_system.x = drawn_system.x
			home_system.y = drawn_system.y
			home_system.wormhole_partner_x = drawn_system.wormhole_partner_x
			home_system.wormhole_partner_y = drawn_system.wormhole_partner_y
			home_system.keep = true
			home_system.is_homeworld = true
			drawn_system.placed = true
			nr_original_possible_monster_locations = nr_original_possible_monster_locations - 1
			break
		end
	end
end

print('placing other systems...')
local next_system_id = 0
local nr_stars_placed = 0
local stars_to_recreate = {}
for i, drawn_system in ipairs(drawn_systems) do
	if drawn_system.placed ~= true then
		next_system_id = get_next_valid_star_id(stars, next_system_id, home_systems)
		if next_system_id ~= -1 then
			local star = stars[next_system_id]
			if star.color == STAR_COLOR_NAME_TO_NUMBER[drawn_system.star_color] or drawn_system.system_type == RANDOM_ENCODING or drawn_system.system_type == BLACK_HOLE_ENCODING then
				star.x = drawn_system.x
				star.y = drawn_system.y
				star.wormhole_partner_x = drawn_system.wormhole_partner_x
				star.wormhole_partner_y = drawn_system.wormhole_partner_y
				star.keep = true
				drawn_system.placed = true
				nr_stars_placed = nr_stars_placed + 1
				if drawn_system.system_type == BLACK_HOLE_ENCODING and star.color ~= BLACK_HOLE_COLOUR_NUMBER then
					star.color = BLACK_HOLE_COLOUR_NUMBER
					star.special = 0
					if star.wormhole ~= -1 then
						stars[star.wormhole] = -1
					end
					star.wormhole = -1
					-- prevent AI from trying to scout black holes by revealing them (humans can't if there are no planets)
					star.visited = 255
					for i, planet in pairs(planets) do
						if planet.star == star.id then
							table.insert(planets_to_delete, planet.id)
						end
					end
				end
			else
				star.color = STAR_COLOR_NAME_TO_NUMBER[drawn_system.star_color]
				star.x = drawn_system.x
				star.y = drawn_system.y
				star.wormhole_partner_x = drawn_system.wormhole_partner_x
				star.wormhole_partner_y = drawn_system.wormhole_partner_y
				star.keep = true
				drawn_system.placed = true
				nr_stars_placed = nr_stars_placed + 1
				table.insert(stars_to_recreate, star.id)
			end
		else
			break
		end
	end
end

if count_dictionary_entries(planets_to_delete) > 0 then
	print('evaporating ' .. tostring(count_dictionary_entries(planets_to_delete)) .. ' unused planets...')
	del_planets(planets_to_delete)
end

collectgarbage()

print('placing wormholes...') -- don't do it earlier, coordinates will not match yet
for s1, star1 in pairs(stars) do
	if star1.wormhole_partner_x ~= nil then
		for s2, star2 in pairs(stars) do
			if star1.wormhole_partner_x == star2.x and star1.wormhole_partner_y == star2.y then
				star1.wormhole = s2
				table.insert(stars_to_recreate, s1)
				table.insert(stars_to_recreate, s2)
				break
			end
		end
	end
end

collectgarbage()

local ships = get_ships()
local ships_to_delete = {}
for i, ship in pairs(ships) do
	if stars[ship.location].color == BLACK_HOLE_COLOUR_NUMBER then
		table.insert(ships_to_delete, i)
	end
end

del_ships(ships_to_delete)
ships_to_delete = nil

local stars_to_delete = {}
for i, star in pairs(stars) do
	if star.keep == nil or star.keep ~= true then
		table.insert(stars_to_delete, i)
	end
end

collectgarbage()

print('updating systems...')
set_stars(stars)

collectgarbage()

print('finding guarding monsters to add special prizes for...')

ships = get_ships()
local star_to_monster_ship = {}
for j, sh in pairs(ships) do
	if sh.player >= 10 and sh.player <= 14 then
		star_to_monster_ship[sh.location] = sh
	end
end

collectgarbage()

-- note: this step can invalidate ids of get_planets and get_ships
print('scheduled ' .. tostring(count_dictionary_entries(stars_to_recreate)) .. ' stars for recreation (including redundant ones that will be skipped)...')
for i, star_to_recreate in pairs(stars_to_recreate) do
	local star = stars[star_to_recreate]
	if star.recreated == nil or star.recreated == false then
		--print('recreating ' .. star.name .. ' (' .. tostring(star.id) .. '), color=' .. tostring(star.color) .. ', special=' .. tostring(star.special) .. ', wormhole=' .. tostring(star.wormhole))
		local partner_star_id = star.wormhole
		local star_x = star.x
		local star_y = star.y
		local star_keep = star.keep

		if partner_star_id ~= -1 then
			-- ensure rerolled at least once and then until it has no special so we can safely use the special for a wormhole
			--print('randomizing ' .. tostring(star.id))
			star = randomize_star(star.id, 0)
			while star.special ~= 0 do
				--print('randomizing ' .. tostring(star.id))
				star = randomize_star(star.id, 0)
			end
			stars[star.id] = star
			star.wormhole = partner_star_id
			print(stars[partner_star_id].wormhole)
			stars[partner_star_id].wormhole = star.id
			print(star)
		elseif star_to_monster_ship[star.id] ~= nil then
			local monster = star_to_monster_ship[star.id]
			-- ensure rerolled at least once and then until it has no special so we can safely use the special for a prize
			--print('randomizing ' .. tostring(star.id))
			star = randomize_star(star.id, 0)
			while (star.special ~= 0 or count_dictionary_entries(star.orbits) == 0) do -- TODO: disclaimer?: no color may be empty on all rolls?
				--print('randomizing ' .. tostring(star.id))
				star = randomize_star(star.id, 0)
			end
			stars[star.id] = star
			--print('upgrading ' .. star.name .. ' with special ' .. tostring(star.special) .. ' for ' .. star_to_monster_ship[star.id].design.name)
			star = upgrade_star_guarded_by_monster(star.id, star_to_monster_ship[star.id].design.name)
			stars[star.id] = star
		else
		    --print('randomizing ' .. tostring(star.id))
			star = randomize_star(star.id, -1)
			stars[star.id] = star
		end
		star.x = star_x
		star.y = star_y
		star.keep = star_keep
		star.recreated = true
	else
		--print('skipping recreation for ' .. tostring(star.id) .. ' as it was already recreated')
	end
	collectgarbage()
end

collectgarbage()

	-- do this here: monsters affect recreation but need updated info (code below still removes monsters at wormholes, we can check for wormholes here beforehand though)
print('checking deviation of new monster density...')

local nr_current_possible_monster_locations = 0
for i, s in pairs(stars) do
	if s.keep == true and s.color ~= BLACK_HOLE_COLOUR_NUMBER and s.wormhole == -1 and (s.is_homeworld == nil or s.is_homeworld == false) and (s.is_orion == nil or s.is_orion == false) and count_dictionary_entries(s.orbits) ~= 0 then
		nr_current_possible_monster_locations = nr_current_possible_monster_locations + 1
	end
end

-- factor 1000 to avoid integer rounding issues; +499 to round up at .5
--print('computing delta: round(1000 * ' .. tostring(nr_original_monsters) .. ' * ' .. tostring(nr_current_possible_monster_locations) .. ') / (1000 * ' .. tostring(nr_original_possible_monster_locations) .. ') - ' .. tostring(count_non_guardian_monsters()))
local desired_nr_of_monsters = (1000 * nr_original_monsters * nr_current_possible_monster_locations) / (nr_original_possible_monster_locations)
--print('desired_nr_of_monsters ' .. tostring(desired_nr_of_monsters))
if desired_nr_of_monsters % 1000 >= 500 then
	--print('rounding up')
	desired_nr_of_monsters = desired_nr_of_monsters + 1000
end
desired_nr_of_monsters = desired_nr_of_monsters / 1000
print(count_non_guardian_monsters())
local monster_delta = desired_nr_of_monsters - count_non_guardian_monsters()
print('applying delta for new nr. of monsters: ' .. tostring(monster_delta) .. '...')

while monster_delta ~= 0 do
	if monster_delta < 0 then
		local ships = get_ships()
		shuffle(ships)
		local ships_to_delete = {}
		for i, sh in pairs(ships) do
			if monster_delta < 0 and sh.player >= 10 and sh.player <= 14 then
				--print('slaying ' .. tostring(sh.design.name) .. ' at ' .. tostring(stars[sh.location].name))
				stars[sh.location] = randomize_star(sh.location, 0)
				monster_delta = desired_nr_of_monsters - count_non_guardian_monsters()
			end
		end
	elseif monster_delta > 0 then
		local upgrade_candidate = -1
		for i, s in pairs(stars) do
			if upgrade_candidate == -1 and s.special == 0 and s.keep == true and s.color ~= BLACK_HOLE_COLOUR_NUMBER and s.wormhole == -1 and (s.is_homeworld == nil or s.is_homeworld == false) and (s.is_orion == nil or s.is_orion == false) and count_dictionary_entries(s.orbits) ~= 0 then
				local valid_candidate = true
				for i, sh in pairs(ships) do
					if sh.location == s.id then -- enough for a check, homeworlds and orion are already excluded
						valid_candidate = false
						break
					end
				end
				if valid_candidate == true then
					upgrade_candidate = s.id
				end
			end
		end
		if upgrade_candidate == -1 then
			msgbox('Zodiac WARNING: could not bring up monster density as desired, missing ' .. tostring(monster_delta) .. ' monster(s).')
		else
			local star = stars[upgrade_candidate]
			local monster_name = ORDINARY_MONSTER_NAMES[random(#ORDINARY_MONSTER_NAMES)]
			--print('spawning ' .. monster_name .. ' at ' .. star.name .. ', upgrading with special ' .. tostring(star.special))
			star = upgrade_star_guarded_by_monster(star.id, monster_name)
			stars[star.id] = star
			monster_delta = desired_nr_of_monsters - count_non_guardian_monsters()
		end
	end
	collectgarbage()
end


print('cleaning up star meta information...')
for i, s in pairs(stars) do
	s.keep = nil
	s.is_orion = nil
	s.is_homeworld = nil
	s.wormhole_partner_x = nil
	s.wormhole_partner_y = nil
end

print('updating systems with recreated and upgraded stars...')
set_stars(stars)

collectgarbage()

print('annihilating ' .. tostring(count_dictionary_entries(stars_to_delete)) .. ' unused systems...')
del_stars(stars_to_delete)
