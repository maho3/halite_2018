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
game.ready("MyPythonBot_v1")


def get_ship_density(me, game_map, pos):
    rho = 0
    sig = 10
    for ship in me.get_ships():
        rho += np.exp(-game_map.calculate_distance(pos,ship.position)**2/(2.*sig**2))
        
    return rho/(2.*np.pi*sig**2)


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
        
        if ship.halite_amount >= constants.MAX_HALITE *2./ 3:
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
        
        if (game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 or ship.is_full):
            poslist = [ship.position] if game_map[ship.position].halite_amount > 0 else []
            
            poslist += [pos for pos in ship.position.get_surrounding_cardinals()  if game_map[pos].is_empty]
                
            pos = ship.position if len(poslist)==0 else max(poslist, key = lambda x: game_map[x].halite_amount )
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
