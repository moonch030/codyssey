#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''계산기 핵심 코어 + PyQt UI 연결 구현.'''

import math
import sys

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QApplication, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget
except ImportError as exc:
    raise SystemExit(
        'PyQt6가 필요하다. 설치: pip install PyQt6\n'
        f'원본 오류: {exc}'
    ) from exc


MAX_ABS_VALUE = 1e15


class Calculator:
    '''사칙연산·부호변환·퍼센트·입력 누적을 담당하는 계산기 코어다.'''

    def __init__(self):
        self.reset()

    def reset(self):
        self.current_text = '0'
        self.accumulator = None
        self.pending_operator = None
        self.waiting_new_number = False
        self.error_state = False

    def _to_float(self):
        return float(self.current_text)

    def _normalize_number(self, value):
        if not math.isfinite(value):
            raise OverflowError('유효한 숫자 범위를 벗어났다.')
        if abs(value) > MAX_ABS_VALUE:
            raise OverflowError('처리 가능한 숫자 범위를 벗어났다.')

        # 보너스: 소수점 6자리 이하 반올림
        rounded = round(value, 6)
        if abs(rounded - int(rounded)) < 1e-12:
            return str(int(rounded))

        text = f'{rounded:.6f}'.rstrip('0').rstrip('.')
        if text == '-0':
            return '0'
        return text

    def _set_error(self):
        self.current_text = '오류'
        self.accumulator = None
        self.pending_operator = None
        self.waiting_new_number = True
        self.error_state = True

    def input_digit(self, digit):
        if self.error_state:
            self.reset()

        if self.waiting_new_number:
            self.current_text = digit
            self.waiting_new_number = False
            return

        if self.current_text == '0':
            self.current_text = digit
        else:
            self.current_text += digit

    def input_decimal(self):
        if self.error_state:
            self.reset()

        if self.waiting_new_number:
            self.current_text = '0.'
            self.waiting_new_number = False
            return

        if '.' not in self.current_text:
            self.current_text += '.'

    def add(self, left, right):
        return left + right

    def subtract(self, left, right):
        return left - right

    def multiply(self, left, right):
        return left * right

    def divide(self, left, right):
        if right == 0:
            raise ZeroDivisionError('0으로 나눌 수 없다.')
        return left / right

    def negative_positive(self):
        if self.error_state:
            return
        value = self._to_float() * -1.0
        try:
            self.current_text = self._normalize_number(value)
        except OverflowError:
            self._set_error()

    def percent(self):
        if self.error_state:
            return
        value = self._to_float() / 100.0
        try:
            self.current_text = self._normalize_number(value)
        except OverflowError:
            self._set_error()

    def _apply_binary(self, left, operator_token, right):
        if operator_token == '+':
            return self.add(left, right)
        if operator_token == '−':
            return self.subtract(left, right)
        if operator_token == '×':
            return self.multiply(left, right)
        if operator_token == '÷':
            return self.divide(left, right)
        raise ValueError('지원하지 않는 연산자다.')

    def set_operator(self, operator_token):
        if self.error_state:
            return

        current_value = self._to_float()

        if self.accumulator is None:
            self.accumulator = current_value
        elif self.pending_operator is not None and not self.waiting_new_number:
            try:
                result = self._apply_binary(self.accumulator, self.pending_operator, current_value)
                self.accumulator = result
                self.current_text = self._normalize_number(result)
            except (ZeroDivisionError, OverflowError, ValueError):
                self._set_error()
                return

        self.pending_operator = operator_token
        self.waiting_new_number = True

    def equal(self):
        if self.error_state:
            return self.current_text

        if self.accumulator is None or self.pending_operator is None:
            return self.current_text

        right = self._to_float()
        try:
            result = self._apply_binary(self.accumulator, self.pending_operator, right)
            self.current_text = self._normalize_number(result)
            self.accumulator = None
            self.pending_operator = None
            self.waiting_new_number = True
            return self.current_text
        except (ZeroDivisionError, OverflowError, ValueError):
            self._set_error()
            return self.current_text


class CalculatorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.core = Calculator()

        self.setWindowTitle('Calculator')
        self.display = QLabel('0')
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.display.setMinimumHeight(96)

        self._set_display_font_by_length('0')

        layout = QVBoxLayout()
        layout.addWidget(self.display)

        grid = QGridLayout()
        grid.setSpacing(8)

        buttons = [
            [('AC', 0, 0), ('±', 0, 1), ('%', 0, 2), ('÷', 0, 3)],
            [('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('×', 1, 3)],
            [('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('−', 2, 3)],
            [('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3)],
        ]

        for row in buttons:
            for text, r, c in row:
                button = QPushButton(text)
                button.setMinimumHeight(64)
                button.clicked.connect(lambda checked, t=text: self._handle_button(t))
                grid.addWidget(button, r, c)

        btn0 = QPushButton('0')
        btn0.setMinimumHeight(64)
        btn0.clicked.connect(lambda: self._handle_button('0'))
        grid.addWidget(btn0, 4, 0, 1, 2)

        btn_dot = QPushButton('.')
        btn_dot.setMinimumHeight(64)
        btn_dot.clicked.connect(lambda: self._handle_button('.'))
        grid.addWidget(btn_dot, 4, 2)

        btn_equal = QPushButton('=')
        btn_equal.setMinimumHeight(64)
        btn_equal.clicked.connect(lambda: self._handle_button('='))
        grid.addWidget(btn_equal, 4, 3)

        layout.addLayout(grid)
        self.setLayout(layout)
        self.resize(360, 520)

    def _set_display_font_by_length(self, text):
        # 보너스: 결과 길이에 따라 폰트 크기를 자동 조정
        n = len(text)
        if n <= 8:
            size = 36
        elif n <= 12:
            size = 30
        elif n <= 16:
            size = 24
        else:
            size = 18

        font = QFont()
        font.setPointSize(size)
        self.display.setFont(font)

    def _sync_display(self):
        text = self.core.current_text
        self.display.setText(text)
        self._set_display_font_by_length(text)

    def _handle_button(self, token):
        if token in '0123456789':
            self.core.input_digit(token)
        elif token == '.':
            self.core.input_decimal()
        elif token in ('+', '−', '×', '÷'):
            self.core.set_operator(token)
        elif token == '=':
            self.core.equal()
        elif token == 'AC':
            self.core.reset()
        elif token == '±':
            self.core.negative_positive()
        elif token == '%':
            self.core.percent()

        self._sync_display()


def main():
    app = QApplication(sys.argv)
    window = CalculatorWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
