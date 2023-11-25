--[[
	Template used when creating a hand-drawn map with the provided tool. v0.4

	Last update of this mod: 8th October 2023; Tested with version 1.50.22 improved

	Questions etc. to: romanhable@web.de (Epirasque)
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

BLACK_HOLE_COLOUR = 6


function shuffle(table_to_shuffle)
	for i = #table_to_shuffle, 2, -1 do
		local j = random(i)
		table_to_shuffle[i], table_to_shuffle[j] = table_to_shuffle[j], table_to_shuffle[i]
	end
end

function initialize_player_dependend_information(players, planets, stars)
	local home_systems = {}
	local nr_players = 0
    for i, player in pairs(players) do
		local home_system = stars[planets[player.home_planet].star]
		nr_players = nr_players + 1
		table.insert(home_systems, home_system)
	end
	return nr_players, home_systems
end

function get_next_valid_star_id(stars, next_star_id, home_systems)
	if next_star_id >= #stars then
		return -1
	end
	while next_star_id < #stars do
		next_star_id = next_star_id + 1
		local star = stars[next_star_id]
		if star.keep == true then
		else
			break
		end
	end
	return next_star_id
end

function go()
	msgbox('Generating Zodiac Map (' .. VERSION .. ', ' .. GALAXY_SIZE .. '):\n' .. TITLE)
	set_stars({}) -- early check that we're in universal context (inspired by hwmirror.lua)
	
	shuffle(drawn_systems) --don't always use the same homeworld locations (also for the same players), same goes for possible orion locations

	local stars = get_stars()
		
	local players = get_players()
	local planets = get_planets()
	
	local nr_players, home_systems = initialize_player_dependend_information(players, planets, stars)
	
	local game = get_game()
	local max_x = game.map_max_x
	local max_y = game.map_max_y	
	local nr_stars = #stars + 1
	
	-- TODO: support for having no orion in the game? or just don't place a marker and it will be removed, seems fine as well
	local orion = stars[0]
	local orion_placed = false
	
	for d, drawn_star in ipairs(drawn_systems) do
		if drawn_star.star_type == ORION_ENCODING and (drawn_star.placed == nil or drawn_star.placed ~= true) then
			if orion_placed == false then
				print('placing orion drawn as ' .. tostring(drawn_star))
				orion_placed = true
				orion.x = drawn_star.x
				orion.y = drawn_star.y
				orion.wormhole_partner_x = drawn_star.wormhole_partner_x
				orion.wormhole_partner_y = drawn_star.wormhole_partner_y
				orion.keep = true
				drawn_star.placed = true
			else
				print('setting orion location as normal one...')
				drawn_star.star_type = NORMAL_SYSTEM_ENCODING
			end
		end
	end

	for p = 1, nr_players do
		local home_system = home_systems[p]
		for j, drawn_star in ipairs(drawn_systems) do
			if drawn_star.star_type == HOMEWORLD_ENCODING and (drawn_star.placed == nil or drawn_star.placed ~= true) then
				print('placing homeworld ' .. tostring(home_system) .. ' drawn as ' .. tostring(drawn_star))
				home_system.x = drawn_star.x
				home_system.y = drawn_star.y
				home_system.wormhole_partner_x = drawn_star.wormhole_partner_x
				home_system.wormhole_partner_y = drawn_star.wormhole_partner_y
				home_system.keep = true
				drawn_star.placed = true
				break
			end
		end
	end
	
	local next_star_id = 0
	for i, drawn_star in ipairs(drawn_systems) do
		if (drawn_star.placed == nil or drawn_star.placed ~= true) then
			next_star_id = get_next_valid_star_id(stars, next_star_id, home_systems)
			local star = stars[next_star_id]
			print('placing ordinary system ' .. tostring(star) .. ' drawn as ' .. tostring(drawn_star))
			star.x = drawn_star.x
			star.y = drawn_star.y
			star.wormhole_partner_x = drawn_star.wormhole_partner_x
			star.wormhole_partner_y = drawn_star.wormhole_partner_y
			star.keep = true
			drawn_star.placed = true
			if drawn_star.star_type == BLACK_HOLE_ENCODING and star.color ~= BLACK_HOLE_COLOUR then
				print('imploding it into a black hole...')
				star.color = BLACK_HOLE_COLOUR
				star.special = 0
				star.wormhole = -1
			end
		end
	end
	
	print('placing wormholes...') -- don't do it earlier, coordinates will not match yet
	for s1, star1 in pairs(stars) do
		if star1.wormhole_partner_x ~= nil then
			for s2, star2 in pairs(stars) do
				if star1.wormhole_partner_x == star2.x and star1.wormhole_partner_y == star2.y then
					print('found a wormhole')
					star1.wormhole = s2
					print(star1)
					break
				end
			end
		end
	end
	
	print('cleaning up monsters at black holes...')
	local ships = get_ships()
	ships_to_delete = {}
	for i, ship in pairs(ships) do
		if stars[ship.location].color == BLACK_HOLE_COLOUR then
			table.insert(ships_to_delete, i)
		end
	end
	del_ships(ships_to_delete)
	
	local stars_to_delete = {}
	for i, star in pairs(stars) do
		if star.keep == nil or star.keep ~= true then
			table.insert(stars_to_delete, i)
		else
			star.keep = nil
		end
	end
	
	print('updating stars...')
	set_stars(stars)
	
	print('cleaning up unused stars...')
	del_stars(stars_to_delete)
	
	
end

go()