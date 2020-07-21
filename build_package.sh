#!/bin/bash
pyinstaller --clean --noconfirm db-playmate.spec
pushd dist
hdiutil create ./DB-Playmate.dmg -srcfolder db-playmate.app -ov
popd
