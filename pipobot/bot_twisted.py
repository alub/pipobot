#!/usr/bin/python
#-*- coding: utf-8 -*-
"""This module contains a class to test the bot in a CLI mode"""

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import logging
import random
from pipobot.bot_test import TestBot, ForgedMsg
from pipobot.lib.unittest import color

logger = logging.getLogger('pipobot.bot_jabber')
colors = ["blue", "cyan", "red", "purple", "yellow"]
colors.extend(["bright %s" % col for col in colors])


class MultiClientEcho(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.username = ""
        self.jid = ""
        self.role = ""
        self.color = random.choice(colors)

    def connectionMade(self):
        self.factory.clients.append(self)
        self.transport.write("Bienvenue !\n")

    def dataReceived(self, data):
        if not self.username:
            username, jid, role = data.strip().split(";")
            self.factory.bot.occupants.add_user(username, jid, role)
            print "%s joined : jid=%s; role=%s" % (username, jid, role)
            self.username = username
            self.jid = jid
            self.role = role
            msg = "*** %s has joined\n" % username
        else:
            msg = "%s %s\n" % (color("<%s>" % self.username, self.color),
                               data.strip())

        #Broadcast message to all clients
        for client in self.factory.clients:
            client.transport.write(msg)

        self.factory.bot.create_msg(self.username, data.strip())

    def connectionLost(self, reason):
        self.factory.clients.remove(self)
        for client in self.factory.clients:
            client.transport.write("*** %s has left\n" % self.username)
        self.factory.bot.occupants.rm_user(self.username)


class MultiClientEchoFactory(Factory):
    def __init__(self, bot):
        self.bot = bot
        self.clients = []

    def buildProtocol(self, addr):
        return MultiClientEcho(self)


class TwistedBot(TestBot):
    def __init__(self, modules, session):
        TestBot.__init__(self, modules, session)
        self.client_facto = MultiClientEchoFactory(self)
        self.color = random.choice(colors)

        reactor.listenTCP(8123, self.client_facto)
        reactor.run()

    def say(self, *args, **kwargs):
        ret = []
        args = args[0]
        if args is not None:
            ret = self.decode_module_message(args)
 
            for client in self.client_facto.clients:
                msg = "%s %s\n" % (color("<%s>" % self.name, self.color),
                                   ret.strip())
                client.transport.write(msg.encode("utf-8"))