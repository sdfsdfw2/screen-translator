#!/bin/bash
set -e

APP_NAME="jietu"
VERSION="1.0.0"
ARCH="amd64"
DEB_DIR="${APP_NAME}_${VERSION}_${ARCH}"

echo "1. 编译 Wails 二进制文件..."
~/go/bin/wails build -platform linux/amd64 -tags webkit2_41 -clean

echo "2. 创建 DEB 目录结构..."
mkdir -p ${DEB_DIR}/DEBIAN
mkdir -p ${DEB_DIR}/usr/local/bin
mkdir -p ${DEB_DIR}/usr/share/applications
mkdir -p ${DEB_DIR}/usr/share/icons/hicolor/256x256/apps

echo "3. 复制编译好的二进制文件..."
cp build/bin/${APP_NAME} ${DEB_DIR}/usr/local/bin/${APP_NAME}
chmod +x ${DEB_DIR}/usr/local/bin/${APP_NAME}

echo "4. 生成 DEBIAN/control 文件..."
cat <<EOF > ${DEB_DIR}/DEBIAN/control
Package: ${APP_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: libgtk-3-0, libwebkit2gtk-4.1-0, libsoup-3.0-0, tesseract-ocr, tesseract-ocr-chi-sim, tesseract-ocr-eng, scrot, libayatana-appindicator3-1
Maintainer: Your Name <your@email.com>
Description: Jietu OCR Screen Translator
 A fast, transparent floating OCR screenshot and translation tool.
EOF

echo "5. 生成桌面快捷方式 (Desktop Entry)..."
cat <<EOF > ${DEB_DIR}/usr/share/applications/${APP_NAME}.desktop
[Desktop Entry]
Name=Jietu OCR
Comment=Screen Translator and OCR Tool
Exec=/usr/local/bin/${APP_NAME}
Icon=${APP_NAME}
Terminal=false
Type=Application
Categories=Utility;
EOF

echo "6. 准备图标..."
# 如果你有一个 jietu.png 图标，请将它替换下方的复制逻辑，这里使用默认的一个如果存在的话
if [ -f "build/appicon.png" ]; then
    cp build/appicon.png ${DEB_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png
elif [ -f "a-solid.png" ]; then
    cp a-solid.png ${DEB_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png
fi

echo "7. 打包 DEB..."
dpkg-deb --build ${DEB_DIR}

echo "打包完成！已生成 ${DEB_DIR}.deb"
