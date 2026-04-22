#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''아이폰 계산기 스타일 UI(PyQt). 보너스: 사칙연산.'''

import sys

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QGridLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:
    raise SystemExit(
        'PyQt6가 필요하다. 예: pip install PyQt6\n'
        f'원본 오류: {exc}'
    ) from exc


OPS = {'+', '-', '\u2212', '\u00d7', '\u00f7'}  # + - − × ÷


def _format_number(value):
    '''실수를 화면에 맞게 짧게 문자열로 만든다.'''
    if value is None:
        return '0'
    try:
        x = float(value)
    except (TypeError, ValueError):
        return '0'

    if abs(x) >= 1e15 or (abs(x) > 0 and abs(x) < 1e-9):
        text = f'{x:.10g}'
    elif abs(x - round(x)) < 1e-12:
        text = str(int(round(x)))
    else:
        text = f'{x:.10g}'.rstrip('0').rstrip('.')
    return text


class Calculator(QWidget):
    '''아이폰 기본 계산기와 같은 5행×4열 배치(0은 가로 2칸).'''

    def __init__(self):
        super().__init__()
        self.setWindowTitle('계산기')

        self._display_text = '0'
        self._stored = None
        self._pending_op = None
        self._waiting_operand = False

        self._display = QLabel(self._display_text)
        self._display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._display.setMinimumHeight(96)
        font = QFont()
        font.setPointSize(34)
        self._display.setFont(font)

        grid = QGridLayout()
        grid.setSpacing(8)

        buttons = [
            [('AC', 0, 0), ('±', 0, 1), ('%', 0, 2), ('\u00f7', 0, 3)],
            [('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('\u00d7', 1, 3)],
            [('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('−', 2, 3)],
            [('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3)],
        ]

        for row in buttons:
            for label, r, c in row:
                btn = QPushButton(label)
                btn.setMinimumHeight(64)
                btn.clicked.connect(lambda checked, t=label: self._on_button(t))
                grid.addWidget(btn, r, c)

        btn0 = QPushButton('0')
        btn0.setMinimumHeight(64)
        btn0.clicked.connect(lambda: self._on_digit('0'))
        grid.addWidget(btn0, 4, 0, 1, 2)

        btn_dot = QPushButton('.')
        btn_dot.setMinimumHeight(64)
        btn_dot.clicked.connect(lambda: self._on_dot())
        grid.addWidget(btn_dot, 4, 2)

        btn_eq = QPushButton('=')
        btn_eq.setMinimumHeight(64)
        btn_eq.clicked.connect(lambda: self._on_equals())
        grid.addWidget(btn_eq, 4, 3)

        layout = QVBoxLayout()
        layout.addWidget(self._display)
        layout.addLayout(grid)
        self.setLayout(layout)

        self.resize(360, 520)

    def _refresh_display(self):
        self._display.setText(self._display_text)

    def _parse_display_value(self):
        try:
            return float(self._display_text.replace(',', ''))
        except ValueError:
            return 0.0

    def _apply_op(self, left, op_token, right):
        if op_token == '+':
            return left + right
        if op_token == '−' or op_token == '-':
            return left - right
        if op_token == '\u00d7' or op_token == '*':
            return left * right
        if op_token == '\u00f7' or op_token == '/':
            if right == 0:
                raise ZeroDivisionError
            return left / right
        raise ValueError('알 수 없는 연산자')

    def _on_digit(self, digit):
        if self._display_text == '오류':
            self._display_text = '0'

        if self._waiting_operand:
            self._display_text = digit
            self._waiting_operand = False
        else:
            if self._display_text == '0' and digit != '0':
                self._display_text = digit
            elif self._display_text == '0' and digit == '0':
                self._display_text = '0'
            else:
                self._display_text += digit

        self._refresh_display()

    def _on_dot(self):
        if self._display_text == '오류':
            self._display_text = '0'

        if self._waiting_operand:
            self._display_text = '0.'
            self._waiting_operand = False
            self._refresh_display()
            return

        if '.' in self._display_text:
            return

        self._display_text += '.'
        self._refresh_display()

    def _all_clear(self):
        self._display_text = '0'
        self._stored = None
        self._pending_op = None
        self._waiting_operand = False
        self._refresh_display()

    def _toggle_sign(self):
        if self._display_text == '오류':
            return
        try:
            value = self._parse_display_value()
        except ValueError:
            return
        value = -value
        self._display_text = _format_number(value)
        self._refresh_display()

    def _percent(self):
        if self._display_text == '오류':
            return
        try:
            value = self._parse_display_value()
        except ValueError:
            return
        value = value / 100.0
        self._display_text = _format_number(value)
        self._refresh_display()

    def _on_operator(self, op_token):
        if self._display_text == '오류':
            return

        cur = self._parse_display_value()

        if self._stored is None:
            self._stored = cur
        elif self._pending_op is not None and not self._waiting_operand:
            try:
                result = self._apply_op(float(self._stored), self._pending_op, cur)
            except ZeroDivisionError:
                self._display_text = '오류'
                self._stored = None
                self._pending_op = None
                self._waiting_operand = True
                self._refresh_display()
                return

            self._stored = result
            self._display_text = _format_number(result)

        self._pending_op = op_token
        self._waiting_operand = True
        self._refresh_display()

    def _on_equals(self):
        if self._display_text == '오류':
            return

        if self._stored is None or self._pending_op is None:
            self._waiting_operand = True
            return

        cur = self._parse_display_value()
        try:
            result = self._apply_op(float(self._stored), self._pending_op, cur)
        except ZeroDivisionError:
            self._display_text = '오류'
            self._stored = None
            self._pending_op = None
            self._waiting_operand = True
            self._refresh_display()
            return

        self._display_text = _format_number(result)
        self._stored = None
        self._pending_op = None
        self._waiting_operand = True
        self._refresh_display()

    def _on_button(self, token):
        if token in '0123456789':
            self._on_digit(token)
            return

        if token == 'AC':
            self._all_clear()
            return

        if token == '±':
            self._toggle_sign()
            return

        if token == '%':
            self._percent()
            return

        if token in OPS:
            self._on_operator(token)
            return


def main():
    app = QApplication(sys.argv)
    window = Calculator()
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
