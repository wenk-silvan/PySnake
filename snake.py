# Author: Silvan Wenk (wenksi)
# Date: 2017/06/22

import random
import sys

from PyQt5.QtCore import QBasicTimer
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication
from copy import copy


class Game(QMainWindow):
    def __init__(self):
        """
        The initial method of the game. This method creates a new game board and sets the layout of the window.
        """
        QMainWindow.__init__(self)

        self._board = Board(self)
        self.setCentralWidget(self._board)

        self._status_bar = self.statusBar()
        self._board.msg_status_bar[str].connect(self._status_bar.showMessage)
        self._board.start()

        board_size = self._board.board_size * self._board.pxl_block_size
        self.move(300, 300)
        self.setFixedSize(board_size, board_size + 20)
        self.setWindowTitle('Snake - by Silvan Wenk')
        self.show()


class CollisionError(Exception):
    """
    Exception class handling if the snake has a collision.
    """
    pass


class Board(QFrame):
    """
    The board class draws the board on which the snake moves. Also the snake itself, food and the enemies.
    The board is managed with squares which move each time the timer event is called. The size and amount of these
    squares are also defined in this class. Always if the second food was eaten, there will spawn an additional enemy.
    """
    msg_status_bar = pyqtSignal(str)
    pxl_block_size = 10
    board_size = 50
    playing = False
    speed = 50

    def __init__(self, parent):
        super().__init__()
        self._timer = QBasicTimer()
        self._new_direction = 2
        self._enemies = []
        self._food = {"x": 0, "y": 0}
        self._snake = None
        self._rand = random.Random()

    def init_board(self):
        self.setStyleSheet("background-color:lightgray;")
        self.setFocusPolicy(Qt.StrongFocus)
        self._enemies = [{"x": 0, "y": 0}]
        self._new_direction = 2
        self._snake = Snake(self.board_size)
        self.spread_food()
        self.move_enemies()

    def paintEvent(self, event):
        """
        The paintEvent is called by the update() function. If the food was eaten since the last timer event,
        new food will be spreaded and the enemies will be replaced randomly on the board.
        :param event:
        """
        painter = QPainter(self)
        self.draw_snake(painter)

        if self._snake.eating:
            self.spread_food()
            if self._snake.body.__len__() % 2 == 0:
                self._enemies.append({"x": 0, "y": 0})
            self.move_enemies()
            self._snake.eating = False

        self.draw_square(painter, self._food["x"], self._food["y"], QColor("green"))
        for enemy in self._enemies:
            self.draw_square(painter, enemy["x"], enemy["y"], QColor("red"))

    def draw_snake(self, painter):
        for part in self._snake.body:
            self.draw_square(painter, part["x"], part["y"], QColor("black"))

    def draw_square(self, painter, x, y, color):
        """
        Draws a square by the coordinates and the block size configuration.
        :param painter:
        :param x:
        :param y:
        :param color:
        :return:
        """
        block_size = self.pxl_block_size
        painter.fillRect(x * block_size, y * block_size, block_size, block_size, color)

    def enemy_forbidden_place(self, enemy):
        """
        Return false if enemy has same coords as food or another enemy
        and if its in the same direction as the snake's head.
        :param enemy:
        :return boolean:
        """
        return ((self._new_direction == 1 or 3) and enemy["y"] == self._snake.head["y"]) \
               or ((self._new_direction == 2 or 4) and enemy["x"] == self._snake.head["x"]) \
               or enemy == self._food \
               or enemy == any(self._enemies)

    def keyPressEvent(self, event):
        key = event.key()
        direction = self._snake.direction
        if key == Qt.Key_Up and direction != 3:
            self._new_direction = 1
        elif key == Qt.Key_Right and direction != 4:
            self._new_direction = 2
        elif key == Qt.Key_Down and direction != 1:
            self._new_direction = 3
        elif key == Qt.Key_Left and direction != 2:
            self._new_direction = 4
        elif key == Qt.Key_Q:
            self.stop()
        elif key == Qt.Key_R and not self.playing:
            self.start()
        else:
            return

    def move_enemies(self):
        for enemy in self._enemies:
            while True:
                enemy["x"] = self._rand.randint(1, self.board_size - 1)
                enemy["y"] = self._rand.randint(1, self.board_size - 1)
                if not self.enemy_forbidden_place(enemy):
                    break

    def stop(self):
        self.msg_status_bar.emit("Game over! ----- Score: " +
                                 str(self._snake.body.__len__() - self._snake.start_length) +
                                 " ----- (Press 'r' to restart the game)")
        self.playing = False
        self._timer.stop()

    def spread_food(self):
        while True:
            self._food["x"] = self._rand.randint(1, self.board_size - 1)
            self._food["y"] = self._rand.randint(1, self.board_size - 1)
            if self._food != self._snake.head:
                break

    def start(self):
        """
        Starts the timer and initializes the game board.
        """
        self.msg_status_bar.emit("Welcome to snake! (Press 'q' to quit the game)")
        self.init_board()
        self.playing = True
        self._timer.start(self.speed, self)

    def timerEvent(self, event):
        """
        Throws exception if snake touched itself, the boarder or an enemy.
        Otherwise the update() function will be called which repaints the game with new coords.
        """
        if event.timerId() == self._timer.timerId():
            self._snake.direction = self._new_direction
            try:
                self._snake.move(self._food, self._enemies)
                self.update()
            except CollisionError:
                self.stop()
        else:
            super(Board, self).timerEvent(event)


class Snake(object):
    """
    The snake class contains the directions of the snake, its length and methods like growing and moving.
    Also there are the methods which check if the snake didn't collide.
    """
    directions = {
        1: "Nord",
        2: "East",
        3: "South",
        4: "West"
    }
    start_length = 10

    def __init__(self, board_size):
        self._board_size = board_size
        self.body = []
        self.direction = 2
        self.eating = False

        for i in reversed(range(self.start_length)):
            self.body.append({"x": i + 2, "y": 2})
        self.head = copy(self.body[0])

    def grow(self):
        self.eating = True
        self.body.append({
            "x": self.body[len(self.body) - 1]["x"],
            "y": self.body[len(self.body) - 1]["y"]})

    def check_head_touches_border(self):
        if self.head["x"] == -1:
            raise CollisionError()
        if self.head["y"] == -1:
            raise CollisionError()
        if self.head["x"] == self._board_size:
            raise CollisionError()
        if self.head["y"] == self._board_size:
            raise CollisionError()

    def check_head_touches_tail(self):
        if any(p == self.head for p in self.body):
            raise CollisionError()

    def head_touches_food(self, food):
        return self.head == food

    def check_head_touches_enemy(self, enemies):
        if any(e == self.head for e in enemies):
            raise CollisionError()

    def move(self, food, enemies):
        """
        If the snake didn't collide, each part of the snake's body gets the coords of the body part ahead.
        The x- or y-axis of the snake's head will increment depending on the direction the snake is moving.
        :param food:
        :param enemies:
        """
        self.set_head_position()

        self.check_head_touches_border()
        self.check_head_touches_tail()
        self.check_head_touches_enemy(enemies)

        if self.head_touches_food(food):
            self.grow()

        for index in reversed(range(self.body.__len__())):
            if index == 0:
                continue
            self.body[index]["x"] = self.body[index - 1]["x"]
            self.body[index]["y"] = self.body[index - 1]["y"]
        self.body[0]["x"] = self.head["x"]
        self.body[0]["y"] = self.head["y"]

    def set_head_position(self):
        if self.direction == 1:
            self.head["y"] -= 1
        elif self.direction == 2:
            self.head["x"] += 1
        elif self.direction == 3:
            self.head["y"] += 1
        elif self.direction == 4:
            self.head["x"] -= 1


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Game()
    sys.exit(app.exec_())
