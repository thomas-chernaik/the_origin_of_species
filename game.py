import time, random, noise, pathfinding
class Game:
    def __init__(self, tickSpeed, mapsize, server):
        self.mapsize = mapsize
        self.server = server#the instance of the server for networking
        self.startTime = time.time()
        self.state = 0#starting, running, finished
        self.players = []#a list of all the players(instances of the species class) in the game
        self.items = []#a list of all the instances of the item class to iterate through when
        self.map = self.generateMap(mapsize)#the map the game takes place in. A grid of a fixed size with random spaces that are not traversable. a 2d array of 1s and 0s
        self.chat = []#the global chat for the game with the time
        self.time = 0#the number of ticks since the beginning of the game
        self.tickSpeed = tickSpeed
        self.creatureSize = 1#this is a magic number
        #tick needs to be called in a seperate thread and recalled every 1/tickspeed seconds

    def generateMap(self, mapsize):
        #generate the map using simplex noise so it looks somewhat realistic if presented in a graphical interface. this should also mean that there are no open spaces that are shut off
        octaves = 1
        freq = 0.15 * mapsize#this means the map will not change based on mapsize
        seed = random.randint(-1000000, 1000000)#if you put a random number generator in a generator it generates a different number each time and becomes random noise so it must be here instead
        map = [[1  if noise.snoise2(x/freq, y/freq, octaves, base=(seed)) > 0.5 else 0 for y in range(mapsize)] for x in range(mapsize)]#for whatever reason the base parameter of this function must be less than 1 million
        return map


    def addSpecies(self, ID):
        #a function to add new players.
        self.updateChat("system: %s has joined the game" % (ID))
        newPlayer = Species(ID, self.creatureSize, self)
        self.players.append(newPlayer)
        newCreatures = newPlayer.firstGeneration()
        self.items += newCreatures
        pass

    def speciesIsDead(self, species):
        #does the appropriate processes when a species dies, including updating the players profile
        self.updateChat("system: %s is extinct" % (species.ID))
        #check if the player wants to quit or spectate. If they want to quit:
        #talk to the server about how they did in the game
        for i in self.players:
            if i == species:
                del(i)
        del(species)
        pass

    def tick(self):
        #this increases the time and tells every item to make decisions, then tells every item to act on the decisions
        self.time += 1
        for item in self.items:
            item.makeDecisions()
        for item in self.items:
            item.move()
        pass

    def pathFind(self, loc1, loc2):
        #this function finds a path between two points and returns the path as a list of tuples
        return pathfinding.astar(self.map, loc1, loc2)


    def plantIsEaten(self, plant):
        #this function removes the plant and adds a new one in a random empty space. An item can be in the space the plant is spawned, but it must not be a hole
        for item in self.items:
            if item == plant:
                del(item)
                del(plant)
                break
        foundEmptySpace=False
        #this just checks the map it doesn't check for other items because multiple items can occupy one space
        while not foundEmptySpace:
            space = (random.randint(0,self.mapsize), random.randint(0,self.mapsize))
            if self.map[space[0]][space[1]] == 0:
                foundEmptySpace = True
        item.append(Plant(self, space, random.randint(1,5), True if random.randint(0,10)==0 else False))#the numbers in the random generators a magic and should be replaced with parameters/class variables

    def updateChat(self, message):
        #updates the chat and updates the chat of every species in the format(time, message
        msg = (time.time(), message)
        self.chat.append(msg)
        for player in self.players:
            player.chat.append(msg)

#the base class for all the different items/creatures that can exist in the game
class Item:
    def __init__(self, game, location, size):
        self.location = location#this is the location of the item on the map
        self.game = game#this is the instance of the game class that the item belongs to. it allows the item to tell the game class to do certain things i.e. if a creature has offspring, a plant is eaten
        self.size = size#this is the size of the item, important for eating

    def isInSight(self, playerLoc):
        #this function checks if the item is visible by the player in playerLoc.
        loc = (playerLoc[0] - self.location[0], playerLoc[1] - self.location[1])
        return loc[0]**2 + loc[1]**2
        pass

    def interestingCharacteristics(self):
        #this function returns the characteristics that affect the decisions that another item might take
        raise Exception("function not implemented")

    def eaten(self):
        # this function does the neccessary processes for if the creature is eaten. It will only be called by the creature that ate it
        raise Exception("function not implemented")

    def move(self):
        #this function exists so we can call this function on  any item and not get an error
        pass

    def makeDecisions(self):
        #this function exists so we can call this function on  any item and not get an error
        pass



class Creature(Item):
    def __init__(self, game, location, size, name, species, characteristics, generation, minPointsEnergy, maxEnergy, ID):
        self.gender = random.randint(0,1)# male = 0 female = 1 only females can have offspring and require a male to do this
        self.ID = (ID, name)#this is used for the family tree and is seperate to the species ID which is the player name. This includes the creature name to make the family tree more readable
        Item.__init__(self, game, location, size)
        self.name = name#a randomly generated name for the creature
        self.age = 0#the age of the item. This doesn't matter for plants. Age is the number of ticks since the item was created.
        self.species = species#the player who owns this creature
        self.characteristics = characteristics#the characteristics of the creature stored in a dictionary with their state i.e. for size this would be the size as a number
        self.energy = maxEnergy#the current energy of the creature. If this reaches zero the creature will die. It decreases with time and movement and increases by eating
        self.offspring = []#this is a list of the IDs of the offspring of this creature. This enables the family tree to be created
        self.generation = generation#the generation that this creature belongs to. Used by the creature class to decide if the player needs to decide new characteristics
        self.minPointsEnergy = minPointsEnergy#the amount of energy required to gain a point when move is called
        self.maxEnergy = maxEnergy#the the maximum energy the creature can have
        self.isBaby = True#the creature is immobile when it is a baby
        self.nextLoc = ()#the location that the creature will move to when move is called
        self.dist = 0

    def calculateMove(self, destination):
        #this function calculates the move for the creature. It will use pathfinding, and return the space that the player should move to based on the speed of the creature
        path = self.game.pathFind(self.location, destination)
        self.dist = min(len(path), self.characteristics["speed"])
        self.nextLoc = path[self.dist]#this will get the speed from the characteristics and move to that space in the path. This means speed is equal to the number of steps moved in one tick

    def move(self):
        #this function moves the creature based on the move from calculateMove. all creatures should be moved at the same time after decisions have all been made. The creatures energy should decrease more if it moves but should always be decreased here. The species points should increase if it has energy over minpointsenergy
        self.energy -= self.dist * self.characteristics["energy per distance moved"] * self.size
        self.location = self.nextLoc

    def haveOffspring(self):
        #this function does the neccessary processes for if the creature wants to have offspring, including prompting the player to make decisions if it is the first offspring of its generation
        self.offspring.append(self.species.addOffspring(self.generation+1))


    def eat(self, item):
        # this function does the necessary processes for if the creature eats something. the amount of energy added should be decided by the size of the item
        if(not self.characteristics["can eat poisonous plants"] and item.__name__ == "Plant"):#sees if it is eating a plant and the creature can be killed by poisonous plants
            if item.poisonous:
                self.species.chat("system: %s ate a poisonous plant and died" % (self.name))
                item.eaten()
                self.dead()

        self.species.updateChat("system: %s ate %s of species %s" % (self.name, item.name, item.species.ID))
        self.energy += self.characteristics["energy per unit size"] * item.size
        item.eaten()
        if self.energy > self.maxEnergy:
            self.energy == self.maxEnergy



    def getInformation(self):
        #this function queries the isInSight of every item and returns a list of all that return true, along with the distance
        itemsInSight = []
        distSquared = self.characteristics["maximum view dist squared"]
        for item in self.game.items:
            itemDist = item.isInSight(self.location)
            if itemDist > distSquared:
                continue
            itemsInSight.append((itemDist, item))
        #sort itemsInSight here using a merge sort and remove the distances
        return itemsInSight

    def makeDecisions(self):
        #this function makes decisions based on its characteristics and the interesting and based on the closest items first. As soon as one decision is made it will be done with this function.

        pass

    def eaten(self, other):
        # this function does the neccessary processes for if the creature is eaten. It will only be called by the creature that ate it
        self.species.updateChat("system: %s was eaten by %s of species %s" % (self.name, other.name, other.species.ID))
        self.dead()

    def dead(self):
        #this function does the necessary processes for if the creature dies
        self.species.creatureIsKilled(self)



class Plant(Item):
    def __init__(self, game, location, size, poisonous):
        Item.__init__(self, game, location, size)
        self.poisonous = poisonous

    def eaten(self):
        # this function does the neccessary processes for if the creature is eaten. It will only be called by the creature that ate it
        self.game.plantIsEaten(self)


class Species:

    def __init__(self, ID, initialSize, game):
        self.game = game
        self.creatureID = 0
        self.creatures = []#a list of all the living creatures in the species
        self.familytree = {}#a graph of all the dead creatures' IDs and
        self.chat = []#a chat containing all of the events specific to this species
        self.ID = ID#the ID of this species that the player who is controlling this species needs to make actions
        self.characteristics = [{"speed" : 0,#the distance that the creature can move per step i time
                                "maximum view dist squared" : 0,#the maximum distance that the creature can see, squared
                                "size" : 0,#the size of the creature
                                 "size can eat" : 0,#the biggest size of creature that this creature can eat, as a ratio
                                 "carnivorous":False,#if the creature can eat other creatures
                                 "number of offspring" : 0,#the number of offspring that will be had by the creature when it has offspring
                                 "time to grow up" : 100,#this is a magic number. also the number of steps in time it will take for the creature to be able to move
                                 "energy per unit size" : 100,#this is a magic number. also the amount of energy that a different creature will gain when eating this creature. this should probably be fixed and not here.
                                 "energy per distance moved" : 100,#this is a magic number. also the amount of energy that will be used by the creature when it is moving
                                 "lifespan" : 0,#the number of steps in time after which the creature will die of old age
                                 "camouflage" : 0,#the chance that another creature won't see this animal. this includes mates
                                 "can recognise predators": False,#if the creature can see predators, and therefore run away
                                 "can eat poison" : False,#if the creature can eat poisonous plants
                                 "can see poison" : False#if the creature can see poisonous plants so it knows not to eat them
                                }]#a list of the characteristics of each generation
        self.points = 0#the points of the species, used to purchase new characteristics. Characteristics cost more the more creatures there are
        self.size = [initialSize]#the size of members of the species as a list split by generations
        self.chatLastRead = time.time()

    def addOffspring(self, generation, parent):
        #adds a new offspring
        if(len(self.characteristics) < generation):
            #tell the server to ask the player to specify the characteristics for the next genreation. it will ignore this if it has already asked
            return#this means that the player hasn't specified the characteristics for this generation yet so this child can't be had.
        if(len(self.characteristics) == generation):#this means that this creature will belong to the youngest generation
            #tell the server to ask the player to specify the characteristics for the next generation
            pass
        newCreature = Creature(self.game, parent.location, self.size[generation-1], self.generateRandomName(), self, self.characteristics[generation-1], generation, 50, 100, 0.1, 0.1, self.creatureID)#these are magic numbers and should be replaced
        self.creatures.append(newCreature)
        self.game.items.append(newCreature)
        self.creatureID += 1


    def generateRandomName(self):
        #choose a random name
        return
    def firstGeneration(self):
        #a function that creates the first genereation of creatures and returns a list of them. The location must be a space on the map with a value of zero
        pass

    def newGeneration(self):
        #called by the server manager when the player responds with the characteristics they want
        #contains the processes so that
        pass
    def sendMessage(self, message):
        #sends a message to the global game chat, and therefore all players
        message = self.ID + ": " + message
        self.game.updateChat(message)
    

    def creatureIsKilled(self, creature):
        #removes the creature from creatures and adds it to the family tree
        self.familytree[creature.ID] = creature.offspring

    def getChat(self):
        #a function to get the unread chat and delete the read chat. This could be made more effecient by deleting the whole chat when it is read, however this is likely to potentially cause issues if there a functions running in different threads
        chat = []#the chat to return, does not include the timestamps
        for message in self.chat:
            if message[0] < self.chatLastRead:
                del(message)
            else:
                chat.append(message[1])
        self.chatLastRead = time.time()
        return chat