#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants

import random
import logging
import numpy as np


# This game object contains the initial game state.
game = hlt.Game()
# Respond with your name.
game.ready("MyPythonBot")

def get_halite_density(game_map, pos, rad=5, sig=2):
    rad = max(rad, 5)
    sig = max(sig, 2)
    
    rho=0
    for i in np.arange(-rad, rad+1):
        for j in np.arange(np.abs(i)-rad, rad-np.abs(i)+1):
            rho+= game_map[pos.directional_offset((i,j))].halite_amount*np.exp(-(i**2 + j**2)/(2*sig**2))
    return rho/(2.*np.pi*sig**2*(2*rad*(2*rad + 1) + 2*(rad-1)*(2*(rad-1)+1))/2)

def get_ship_density(me, game_map, pos, sig=10):
    if len(me.get_ships())==0: return 0
    
    rho = 0
    for ship in me.get_ships():
        rho += np.exp(-game_map.calculate_distance(pos,ship.position)**2/(2.*sig**2))
        
    return rho/(2.*np.pi*sig**2)

mid_phase=25
end_phase=100

ship_status = {}
ship_prev = {}

while True:
    # Get the latest game state.
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []

    for ship in me.get_ships():
        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.
        
        if ship.halite_amount >= constants.MAX_HALITE * ((2./3) if game.turn_number < mid_phase else (9./ 10)):
            ship_status[ship.id] = "returning"
            
        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"
        
        if ship.halite_amount < 0.1*game_map[ship.position].halite_amount and ship.position != me.shipyard.position:
            command_queue.append(ship.stay_still())
            game_map[ship.position].mark_unsafe(ship)
            continue
        
        if ship_status[ship.id] == "returning":
            if ship.position == me.shipyard.position:
                ship_status[ship.id] = "exploring"
            else:
                move = game_map.naive_navigate(ship, me.shipyard.position)
                command_queue.append(ship.move(move))
                continue
        
        if (game_map[ship.position].halite_amount < constants.MAX_HALITE / (10 if game.turn_number < end_phase else 20) or ship.is_full):
            poslist = [ship.position] if game_map[ship.position].halite_amount > 0 else []
            
            poslist += [pos for pos in ship.position.get_surrounding_cardinals()  if game_map[pos].is_empty]
            
            d_to_home = game_map.calculate_distance(ship.position, me.shipyard.position)
                
            pos = ship.position if len(poslist)==0 else max(poslist, key = (lambda x: game_map[x].halite_amount) if game.turn_number < mid_phase else (lambda x: game_map[x].halite_amount*get_halite_density(game_map, x, rad=int(d_to_home/4), sig=int(d_to_home/8))) )
            if pos!=ship.position or pos == me.shipyard.position:
            
                command_queue.append(ship.move(game_map.naive_navigate(ship,pos)))
                continue
        
        command_queue.append(ship.stay_still())
        game_map[ship.position].mark_unsafe(ship)

    # If you're on the first turn and have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though.
    if (game.turn_number-1)%1 == 0 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        logging.info(str(get_ship_density(me, game_map, me.shipyard.position)))
        if get_ship_density(me, game_map, me.shipyard.position) < 0.01:
            command_queue.append(game.me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
