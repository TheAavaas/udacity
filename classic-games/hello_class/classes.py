#!/usr/bin/env python
# game.py - simple game to demonstrate classes and objects
import random
from lib import *

CHR_PLAYER = "S"
CHR_ENEMY = "B"
CHR_WIZARD = "W"
CHR_ARCHER = "A"
CHR_DEAD = "X"
CHR_CHEST = "#"
CHR_ITEM = "*"

INVENTORY_SIZE = 5

class StatusBar(object):
    def __init__(self, character = None):
        self.character = character
        self.msg = ''
    
    def set_character(self, character):
        self.character = character
        self.set_status()
        self.show()
        
    def set_status(self, msg = ''):
        self.msg = (msg, '::'.join((self.msg, msg)))[len(self.msg) > 0]
        status = "HP: %i/%i" % (self.character.hp, self.character.max_hp)
        msgs = self.msg.split('::')
        
        self.line1 = "%s + %s" % (status, msgs[0])
        if len(msgs) > 1:
            self.line2 = "%s + %s" % (' ' * len(status), msgs[1])
        else:
            self.line2 = "%s + %s" % (' ' * len(status), ' ' * len(msgs[0]))

    def format_line(self, txt, width):
        line = "+ %s" % txt
        line += " " * (width - (len(line))) + " +"
        return line

    def show(self):
        self.set_status()
        print "+" * (world.width + 2)
        print self.format_line(self.line1, world.width)
        print self.format_line(self.line2, world.width)
        self.msg = ''

statusbar = StatusBar()

class WorldMap(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.map = [[None for y in range(self.height)] for x in range(self.width)]

    def is_occupied(self, x, y):
        ''' Checks if a given space on the map and returns True if occupied. '''
        return self.map[x][y] is not None

    def print_map(self):
        print '+' * (self.width + 2)
        for y in range(self.height - 1, 0, -1):
            line = '+'
            for x in range(self.width):
                cell = self.map[x][y]
                if cell is None:
                    line += ' '
                else:
                    line += cell.image
            print line + '+'
        print '+' * (self.width + 2)

world = WorldMap(60, 22)

#world = [[None for x in range(100)] for y in range(100)]

class Entity:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image
        
        if x and y:
            self.occupy()
    
    def occupy(self):
        world.map[self.x][self.y] = self

    def remove(self):
        world.map[self.x][self.y] = None

    def distance(self, other):
        return abs(other.x - self.x), abs(other.y - self.y)

class Item(Entity):
    def __init__(self, name, x = None, y = None):
        Entity.__init__(self, x, y, CHR_ITEM)
        self.name = name
        
class Weapon(Item):
    def __init__(self, name, damage, attack_range = 1, x = None, y = None):
        Item.__init__(self, name, x, y)
        self.damage = damage
        # not yet used
        self.attack_range = attack_range

class Chest(Entity):
    def __init__(self, x, y, items = []):
        Entity.__init__(self, x, y, CHR_CHEST)
        self.items = items
        
    def open(self):
        if len(self.items):
            statusbar.set_status("Chest: %s" % format_items(self.items))
        else:
            statusbar.set_status("Chest is empty.")

class Character(Entity):
    def __init__(self, x, y, image, hp, damage = 10):
        Entity.__init__(self, x, y, image)
        self.hp, self.max_hp = hp, hp
        self.damage = damage
        self.items = []

    def _direction_to_dxdy(self, direction):
        """Convert a string representing movement direction into a tuple
        (dx, dy), where 'dx' is the size of step in the 'x' direction and
        'dy' is the size of step in the 'y' direction."""
        dx, dy = 0, 0
        if direction == 'left':
            dx = -1
        elif direction == 'right':
            dx = 1
        elif direction == 'up':
            dy = 1
        elif direction == 'down':
            dy = -1
        return dx, dy

    def new_pos(self, direction):
        '''
            Calculates a new position given a direction. Takes as input a 
            direction 'left', 'right', 'up' or 'down'. Allows wrapping of the 
            world map (eg. moving left from x = 0 moves you to x = -1)
        '''
        dx, dy = self._direction_to_dxdy(direction)
        new_x = (self.x + dx) % world.width
        new_y = (self.y + dy) % world.height
        return new_x, new_y

    def move(self, direction):
        """
            Moves the character to the new position.
        """
        # No action if dead X-(
        if not self.hp:
            return False
            
        new_x, new_y = self.new_pos(direction)
        if world.is_occupied(new_x, new_y):
            statusbar.set_status('Position is occupied, try another move.')
        else:
            self.remove()
            self.x, self.y = new_x, new_y
            self.occupy()

    def attack(self, enemy):
        # No action if dead X-(
        if not self.hp:
            return False
            
        dist = self.distance(enemy)
        if dist == (0, 1) or dist == (1, 0):
            if not enemy.hp:
                # just for fun
                msgs = [
                    "This body doesn't look delicious at all.",
                    "You really want me to do this?",
                    "Yeah, whatever!",
                    "I killed it! What did you make me do!"
                    ]
                statusbar.set_status(random.choice(msgs))
            else:
                # Possible damage is depending on physical condition
                worst = int((self.condition() * 0.01) ** (1/2.) * self.damage + 0.5)
                best = int((self.condition() * 0.01) ** (1/4.) * self.damage + 0.5)
                damage = (worst == best) and best or random.randint(worst, best)
                
                # Possible damage is also depending on sudden adrenaline
                # rushes and aiming accuracy or at least butterfly flaps
                damage = random.randint(
                    (damage-1, 0)[not damage],
                    (damage+1, self.damage)[damage == self.damage])
                    
                # Check if character class has weapon attribute and character uses a weapon
                if hasattr(self, 'weapon') and self.weapon:
                    damage += self.weapon.damage
                    
                enemy.harm(damage)
                
                if enemy.image == CHR_PLAYER:
                    statusbar.set_status("You are being attacked: %i damage." % damage)
                elif self.image == CHR_PLAYER:
                    if enemy.image == CHR_DEAD:
                        statusbar.set_status("You make %i damage: your enemy is dead." % damage)
                    else:
                        statusbar.set_status("You make %i damage: %s has %i/%i hp left." % \
                            (damage, enemy.image, enemy.hp, enemy.max_hp))
        else:
            # import fun
            msgs = [
                "Woah! Kicking air really is fun!",
                "This would be totally ineffective!",
                "Just scaring the hiding velociraptors..."
                ]
            statusbar.set_status(random.choice(msgs))

    def condition(self):
        return (self.hp * 100) / self.max_hp

    def harm(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.image = CHR_DEAD
            self.hp = 0

    def get_all_enemies_at_distance(self, dist):
        """Return a list of all enemies that are exactly 'dist' cells away
        either horizontally or vertically.
        """
        coords = [((self.x + dist) % world.width, self.y % world.height),
                  ((self.x - dist) % world.width, self.y % world.height),
                  (self.x % world.width, (self.y + dist) % world.height),
                  (self.x % world.width, (self.y - dist) % world.height)]
        enemies = []
        for x, y in coords:
            if world.is_occupied(x, y) and isinstance(world.map[x][y], Enemy):
                enemies.append(world.map[x][y])
        return enemies

    def get_all_enemies(self, max_dist=1):
        """Return a list of all enemies that are at most 'max_dist' cells away
        either horizontally or vertically.
        """
        enemies = []
        for dist in range(1, max_dist+1):
            enemies.extend(self.get_all_enemies_at_distance(dist))
        return enemies

    def get_alive_enemies_at_distance(self, dist):
        """Return a list of alive enemies that are exactly 'dist' cells away
        either horizontally or vertically.
        """
        enemies = self.get_all_enemies_at_distance(dist)
        return [enemy for enemy in enemies if enemy.hp > 0]

    def get_alive_enemies(self, max_dist=1):
        """Return a list of alive enemies that are at most 'max_dist' cells away
        either horizontally or vertically.
        """
        enemies = self.get_all_enemies(max_dist)
        return [enemy for enemy in enemies if enemy.hp > 0]

class Player(Character):
    def __init__(self, x, y, hp):
        Character.__init__(self, x, y, CHR_PLAYER, hp)
        self.weapon = False
        
    def show_items(self):
        statusbar.set_status(format_items(self.items))
        
    def carry_item(self, item):
        if len(self.items) < INVENTORY_SIZE:
            self.items.append(item)
            statusbar.set_status("%s is now in your inventory." % item.name)
            return True
        else:
            statusbar.set_status("You can't carry that much.")
            return False
    
    # not yet used and untested
    def drop(self, pos):
        """ Drops items from the inventory. Chests are preferred.
            Otherwise items are dropped to the ground nearby.
        """
        if pos not in range(len(self.items)):
            statusbar.set_status("You don't have that many items.")
            return False
            
        item = self.items.pop(pos)
        name = item.name
        
        chests = []
        for direction in ['left','right','up','down']:
            x, y = self.new_pos(direction)
            if world.is_occupied(x, y) and isinstance(world.map[x][y], Chest):
                chests.append(world.map[x][y])
                break
        
        if item == self.weapon:
            self.weapon = False
                
        if len(chests):
            chests[0].items.append(item)
        else:
            for direction in ['left','right','up','down']:
                x, y = self.new_pos(direction)
                if not world.is_occupied(x, y):
                    item.x, item.y = x, y
                    item.occupy()
                    break
                    
        statusbar.set_status("%s dropped." % name)
    
    def draw_weapon(self, pos):
        if pos in range(len(self.items)):
            if isinstance(self.items[pos], Weapon):
                self.weapon = self.items[pos]
                statusbar.set_status("The %s increases your damage by %i points." \
                    % (self.weapon.name, self.weapon.damage))
            else:
                statusbar.set_status("Item is no weapon. It's a %s." % self.items[pos].name)
        else:
            statusbar.set_status("You don't have that many items.")
    
    def open(self):
        """ Checks if anything openable is around and if true
            calls the open method of the object.
        """
        for direction in ['left','right','up','down']:
            x, y = self.new_pos(direction)
            # tuple of openable classes like doors etc.
            # NEEDS TO BE A TUPLE!
            possibles = (Chest)
            if world.is_occupied(x, y) and isinstance(world.map[x][y], possibles):
                world.map[x][y].open()
                return
        
        statusbar.set_status("Nothing to open around.")
            
    def pick(self, n = None):
        # checkout if anything openable is around
        for direction in ['left','right','up','down']:
            x, y = self.new_pos(direction)
            # tuple of pickable classes like Items, Chests etc.
            # NEEDS TO BE A TUPLE!
            if world.is_occupied(x, y):
                if isinstance(world.map[x][y], Item):
                    self.carry_item(world.map[x][y])
                    # don't display item on map if picked up
                    world.map[x][y].remove()
                    return
                if isinstance(world.map[x][y], Chest):
                    if n in range(len(world.map[x][y].items)):
                        item = world.map[x][y].items[n]
                        if self.carry_item(item):
                            world.map[x][y].items.remove(item)
                    else:
                        statusbar.set_status("Specify which item to pick.")
                    return
                     
        statusbar.set_status("Nothing to pick up.")
            
class Enemy(Character):
    def __init__(self, x, y, hp):
        Character.__init__(self, x, y, CHR_ENEMY, hp)

    # not yet used
    def challenge(self, other):
        print "Let's fight!"
        
    def act(self, character, directions):
        choices = [0, 1]
        
        dist = self.distance(character)
        if dist == (0, 1) or dist == (1, 0):
            choices.append(2)
        choice = random.choice(choices)
        
        if choice == 1:
            # Moving
            while (True):
                goto = directions[random.choice(directions.keys())]
                new_x, new_y = self.new_pos(goto)
                if not world.is_occupied(new_x, new_y):
                    self.move(goto)
                    break
        elif choice == 2:
            # Fighting back
            self.attack(character)

class Wizard(Character):
    def __init__(self, x, y, hp):
        Character.__init__(self, x, y, CHR_WIZARD, hp)

    def cast_spell(self, name, target):
        """Cast a spell on the given target."""
        if name == 'remove':
            self._cast_remove(target)
        elif name == 'hp-stealer':
            self._cast_hp_stealer(target)
        else:
            print "The wizard does not know the spell '{0}' yet.".format(name)

    def _cast_remove(self, enemy):
        dist = self.distance(enemy)
        if dist == (0, 1) or dist == (1, 0):
            enemy.remove()

    def _cast_hp_stealer(self, enemy):
        dist = self.distance(enemy)
        if dist == (0, 3) or dist == (3, 0):
            enemy.harm(3)
            self.hp += 3

class Archer(Character):
    def __init__(self, x, y, hp):
        Character.__init__(self, x, y, CHR_ARCHER, hp)
    
    def range_attack(self, enemy):
        dist = self.distance(enemy)
        if (dist[0] <= 5 and dist[1] == 0) or (dist[0] == 0 and dist[1] <= 5):
            enemy.harm(5)
