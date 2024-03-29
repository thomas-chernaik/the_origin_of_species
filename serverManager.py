import game
import string
import time
import random
import threading
import mylogging
import database
class ServerManager:
    @mylogging.log
    def __init__(self):
        self.lock = threading.Lock()
        self.games = {}#a dictionary with the key as the id of each games and the value as a tuple of the game instance and the time it was started at and the name of the creator
        self.players = {}# a dictionary with the key as the string sent to the user when they log in and the value as a tuple of the player name and the time they logged in and the id of the game they are in
        self.newGenerations = {}# a dictionary with the key as the player name and the value as a tuple with the number of generations they need to choose characteristics for and the number of points they have and the existing characteristics
        self.characteristicsCost = {"speed" : (20, 0),#the distance that the creature can move per step i time
                                "maximum view dist squared" : (1, 0),#the maximum distance that the creature can see, squared
                                 "size can eat" : (1000, 0),#the biggest size of creature that this creature can eat, as a ratio
                                 "carnivorous":(100, 0),#if the creature can eat other creatures
                                 "number of offspring" : (50, 0),#the number of offspring that will be had by the creature when it has offspring
                                 "time to grow up" : (100, 100),#multiply this by 100-the value. also the number of steps in time it will take for the creature to be able to move
                                 "energy per unit size" : (100, 100),#multiply this by 100 - the value. also the amount of energy that a different creature will gain when eating this creature. this should probably be fixed and not here.
                                 "energy per distance moved" : (100, 100),#also the amount of energy that will be used by the creature when it is moving
                                 "lifespan" : (1, 0),#the number of steps in time after which the creature will die of old age
                                 "camouflage" : (1000, 0),#the chance that another creature won't see this animal. this includes mates
                                 "can recognise predators": (100, 0),#if the creature can see predators, and therefore run away
                                 "can eat poison" : (1000, 0),#if the creature can eat poisonous plants
                                 "can see poison" : (200, 0),#if the creature can see poisonous plants so it knows not to eat them
                                 "chance to have offspring" : (1000, 10)#1/ the probability that an offspring will be had at a given opportunity
                                }#a dictionary of the cost of characteristics. first value is cost second value is how you get things that decrease to increase by doing abs(cost[1] - num) * cost. the numbers here are just chosen randomly from my brain right now and should be changed to improve gameplay

        self.maxCharacteristics = {"speed" : (100, True),#the distance that the creature can move per step i time
                                "maximum view dist squared" : (100, True),#the maximum distance that the creature can see, squared
                                 "size can eat" : (2, True),#the biggest size of creature that this creature can eat, as a ratio
                                 "carnivorous":(1, True),#if the creature can eat other creatures
                                 "number of offspring" : (10, True),#the number of offspring that will be had by the creature when it has offspring
                                 "time to grow up" : (10, False),#the number of steps in time it will take for the creature to be able to move
                                 "energy per unit size" : (10, False),#the amount of energy that a different creature will gain when eating this creature. this should probably be fixed and not here.
                                 "energy per distance moved" : (10, False),#also the amount of energy that will be used by the creature when it is moving
                                 "lifespan" : (1000, True),#the number of steps in time after which the creature will die of old age
                                 "camouflage" : (0.75, True),#the chance that another creature won't see this animal. this includes mates
                                 "can recognise predators": (1, True),#if the creature can see predators, and therefore run away
                                 "can eat poison" : (1, True),#if the creature can eat poisonous plants
                                 "can see poison" : (1, True),#if the creature can see poisonous plants so it knows not to eat them
                                 "chance to have offspring" : (0.75, True)#1/ the probability that an offspring will be had at a given opportunity
                                }#a dictionary for the max values of each characteristic. is False if it is a minimum

    @mylogging.log
    @property
    def maxCharacteristics(self):
        return self.__maxCharacteristics

    @mylogging.log
    @maxCharacteristics.setter
    def maxCharacteristics(self, value):
        self.__maxCharacteristics = value

    @mylogging.log
    @property
    def characteristicsCost(self):
        return self.__characteristicsCost

    @mylogging.log
    @characteristicsCost.setter
    def characteristicsCost(self, value):
        self.__characteristicsCost = value

    @mylogging.log
    @property
    def newGenerations(self):
        return self.__newGenerations

    @mylogging.log
    @newGenerations.setter
    def newGenerations(self, value):
        self.__newGenerations = value

    @mylogging.log
    @property
    def players(self):
        return self.__players

    @mylogging.log
    @players.setter
    def players(self, value):
        self.__players = value

    @mylogging.log
    @property
    def games(self):
        return self.__games

    @mylogging.log
    @games.setter
    def games(self, value):
        self.__games = value

    @mylogging.log
    @property
    def lock(self):
        return self.__lock

    @mylogging.log
    @lock.setter
    def lock(self, value):
        self.__lock = value

    @mylogging.log
    def checkCharacteristicsAreValid(self, characteristics, points, size):
        #check that all the characteristics are less than the maxCharacteristics
        for characteristic in characteristics.keys():
            if self.maxCharacteristics[characteristics][1]:
                if characteristics[characteristic] > self.maxCharacteristics[characteristics][0]:
                    return False
            else:
                if characteristics[characteristic] < self.maxCharacteristics[characteristics][0]:
                    return False

        #check that the characteristics cost the amount of points the player has
        count = size * 10
        for characteristic in characteristics.keys():
            count += abs(self.characteristicsCost[characteristic][1] - characteristics[characteristic]) * self.characteristicsCost[characteristic][0]
        return count == points

    @mylogging.log
    def logIn(self, username):
        #the password will have already been checked in the flask file with the database
        #the username will contain the players username as well as any titles they have unlocked
        toDelete = []
        for id in self.players.keys():
            if self.players[id][0] == username:
                toDelete.append(id)
        for i in toDelete:
            del(self.players[i])
        uniqueString = self.generateUniqueString(50)
        self.players[uniqueString] = [username, time.time(), None]
        return uniqueString

    @mylogging.log
    def getUsername(self, uniqueString):
        return self.players[uniqueString][0]

    @mylogging.log
    def updateName(self, newName, playerID):
        self.players[playerID] = (newName, self.players[playerID][1], self.players[playerID][2])

    @mylogging.log
    def generateUniqueString(self, length):
        #method from here https://www.educative.io/edpresso/how-to-generate-a-random-string-in-python
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(length))

    @mylogging.log
    def newGame(self, creatorID, maxPlayers):
        id = self.generateUniqueString(5)
        self.games[id] = [game.Game(500, self, maxPlayers), time.time(), self.players[creatorID][0]]
        return id

    @mylogging.log
    def joinGame(self, playerID, gameID):
        self.games[gameID][0].addSpecies(self.players[playerID][0])
        self.players[playerID][2] = self.games[gameID][0]

    @mylogging.log
    def startGame(self, playerID, gameID):
        #this starts the game the player is in if the player is the creator
        if self.games[gameID][2] == self.players[playerID][0]:
            self.games[gameID][0].started = True
            return True
        return False

    @mylogging.log
    def getChat(self, playerID):
        if self.players[playerID][2]:
            return self.players[playerID][2].getChat(self.players[playerID][0])
        else:
            return ""#"you aren't currently in a game im confused why you would ask this"

    @mylogging.log
    def tick(self, timeBetweenTicks):
        #this function should be called in a seperate thread and will constantly tick the server
        while True:
            #print("hey1")
            timer = time.time()
            self.lock.acquire()
            #if security is a concern(which it currently isn't) you would check that all of the players haven't been logged in for too long
            for gameID in self.games:
                if self.games[gameID][1] - time.time() > 10800:#this means that if a game is older than 3 hours it will be deleted. this may need to be extended and is a magic number
                    del(self.games[gameID])
                else:
                    self.games[gameID][0].tick()
            self.lock.release()
            if time.time() - timer < timeBetweenTicks:
                time.sleep(timeBetweenTicks - (time.time() - timer))
            else:
                #if this is ever reached then that means that the tick speed specified is too fast as the server cannot keep up.
                print("error: server running slower than designated tick speed")
                self.lock.release()#because otherwise if it is running below tick speed the lock will never be released
                time.sleep(0.1)

    @mylogging.log
    def checkForNewGeneration(self, ID):
        #this function should be called by the client when getChat is called and will tell them if they need to define a new generation, and how
        if self.players[ID][2]:#if the player is in a game
            if self.players[ID][2].players[self.players[ID][0]].doesNeedNewGeneration:
                return self.players[ID][2].players[self.players[ID][0]].points#only the points need to be returned as the client should remember the last generation's characteristics
        else:
            return None#no new generation is needed

    @mylogging.log
    def newGeneration(self, characteristicslist, size, ID):
        #this function should be called by the client when the player has defined a new generation
        characteristics = {"speed": 1,  # the distance that the creature can move per step i time
                           "maximum view dist squared": 1,  # the maximum distance that the creature can see, squared
                           "size can eat": 0,  # the biggest size of creature that this creature can eat, as a ratio
                           "carnivorous": 0,  # if the creature can eat other creatures
                           "number of offspring": 1,
                           # the number of offspring that will be had by the creature when it has offspring
                           "time to grow up": 100,
                           # the number of steps in time it will take for the creature to be able to move
                           "energy per unit size": 100,
                           # the amount of energy that a different creature will gain when eating this creature. this should probably be fixed and not here.
                           "energy per distance moved": 100,
                           # also the amount of energy that will be used by the creature when it is moving
                           "lifespan": 100,  # the number of steps in time after which the creature will die of old age
                           "camouflage": 0,
                           # the chance that another creature won't see this animal. this includes mates
                           "can recognise predators": 0,  # if the creature can see predators, and therefore run away
                           "can eat poison": 0,  # if the creature can eat poisonous plants
                           "can see poison": 0,  # if the creature can see poisonous plants so it knows not to eat them
                           "chance to have offspring": 0
                           # 1/ the probability that an offspring will be had at a given opportunity
                           }
        for i, key in enumerate(characteristics.keys()):
            characteristics[key] = characteristicslist[i]
        if self.checkCharacteristicsAreValid(characteristics, self.players[ID][2].players[self.players[ID][0]].points, size):
            self.players[ID][2].players[self.players[ID][0]].newGeneration(characteristics, size)
            return True
        return False

    @mylogging.log
    def sendMessage(self, message, ID):
        #this function contains the processes for the message to be sent to all the players.
        try:
            self.players[ID][2].players[self.players[ID][0]].sendMessage(message)
            return True
        except:
            print("someone tried to send a message and failed")
            return False

    @mylogging.log
    def quitGame(self, ID):
        self.players[ID][2] = None

    @mylogging.log
    def unlockCosmetic(self, player, cosmeticID):
        database.unlockNewCosmetic(player, cosmeticID)
