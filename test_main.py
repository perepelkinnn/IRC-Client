import unittest
import main
import sys


main.is_running = True


class TestConfig(unittest.TestCase):
    def test_init(self):
        config = main.Config('testserver', 'testnick')
        self.assertEqual(config.nickname, 'testnick')
        self.assertEqual(config.server, 'testserver')


class TestCommands(unittest.TestCase):
    def test_privmsg(self):
        res = main.Commands.privmsg('testtarget', 'testmsg')
        self.assertEqual(res, 'PRIVMSG testtarget : testmsg\r\n')

    def test_user(self):
        res = main.Commands.user('nick', 'host', 'server')
        self.assertEqual(res, 'USER nick host server nick\r\n')

    def test_join(self):
        res = main.Commands.join('channel')
        self.assertEqual(res, 'JOIN channel\r\n')

    def test_command_part(self):
        res = main.Commands.part('channel')
        self.assertEqual(res, 'PART channel\r\n')

    def test_pong(self):
        res = main.Commands.pong('server')
        self.assertEqual(res, 'PONG server\r\n')

    def test_nick(self):
        main.__channel__ = None
        res = main.Commands.nick('nick')
        self.assertEqual(res, 'NICK nick\r\n')
        main.__channel__ = 'channel'
        res = main.Commands.nick('nick')
        self.assertEqual(res, 'NICK nick\r\nNAMES channel\r\n')

    def test_quit(self):
        res = main.Commands.quit()
        self.assertEqual(res, 'QUIT \r\n')
        res = main.Commands.quit('msg')
        self.assertEqual(res, 'QUIT msg\r\n')

    def test_command_names(self):
        main.__channel__ = None
        res = main.Commands.names()
        self.assertEqual(res, None)
        main.__channel__ = 'channel'
        res = main.Commands.names()
        self.assertEqual(res, 'NAMES channel\r\n')


class Socket:
    def __init__(self):
        self.input = []
        self.output = []

    def get(self):
        if self.input:
            return self.output.pop(0)
        else:
            return ''

    def send(self, cmd):
        if cmd:
            self.input.append(cmd)


class TestHandler(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.handler = main.Handler(Socket())

    def test_pre_parse(self):
        res = self.handler.pre_parse_msg(
            ':haski!~haski@212.193.78.200 JOIN #716')
        print(res)
        self.assertTupleEqual(
            res, ('haski!~haski@212.193.78.200', 'JOIN', ['#716']))

    def test_sort_nicks(self):
        nicks = ['nick1', '@nick2', 'nick3', '@nick4']
        res = self.handler.sort_nicks(nicks)
        self.assertListEqual(res, ['@nick2', '@nick4', 'nick1', 'nick3'])

    def test_parse_prvmsg(self):
        res = self.handler.parse_msg('nick', 'PRIVMSG', ['channel', 'msg'])
        self.assertEqual(res, '<nick> msg')

    def test_parse_join(self):
        res = self.handler.parse_msg('nick', 'JOIN', ['channel'])
        self.assertEqual(res, '<nick> join to channel')

    def test_parse_quit(self):
        res = self.handler.parse_msg('nick', 'QUIT', ['channel'])
        self.assertEqual(res, '<nick> left from channel')


class TestClient(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.client = main.Client('server', 'nick', Socket())

    def setUp(self):
        main.__channel__ = None
        self.client.socket.input = []
        self.client.socket.output = []

    def test_login(self):
        self.client.login()
        res = self.client.socket.input
        expected = ['USER nick {} server nick\r\n'.format(
            self.client.config.hostname), 'NICK nick\r\n']
        self.assertListEqual(res, expected)

    def test_join(self):
        self.client.join('channel')
        res = self.client.socket.input
        expected = ['JOIN channel\r\n']
        self.assertListEqual(res, expected)

    def test_left(self):
        self.client.left('channel')
        res = self.client.socket.input
        expected = ['PART channel\r\n']
        self.assertListEqual(res, expected)

    def test_change_nick(self):
        self.client.change_nick('nick')
        res = self.client.socket.input
        expected = ['NICK nick\r\n']
        self.assertListEqual(res, expected)

    def test_short_message(self):
        self.client.config.target = 'channel'
        self.client.send_message('msg')
        res = self.client.socket.input
        expected = ['PRIVMSG channel : msg\r\n']
        self.assertListEqual(res, expected)

    def test_long_message(self):
        self.client.config.target = 'channel'
        self.client.send_message('a' * 256)
        res = self.client.socket.input
        expected = ['PRIVMSG channel : {}\r\n'.format(
            'a'*255), 'PRIVMSG channel : a\r\n']
        self.assertListEqual(res, expected)


if __name__ == '__main__':
    unittest.main()
