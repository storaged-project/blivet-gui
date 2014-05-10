#!/bin/sh

xgettext --language=Python --from-code=utf-8 --keyword=_ --output=po/blivet-gui.pot `find . -name "../*.py"`