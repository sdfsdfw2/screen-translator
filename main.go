package main

import (
	"embed"
	"fmt"
	"os"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
	"github.com/wailsapp/wails/v2/pkg/options/linux"
	"github.com/wailsapp/wails/v2/pkg/runtime"
	"github.com/yourusername/jietu/backend"

	"github.com/energye/systray"
)

//go:embed all:frontend/dist
var assets embed.FS

//go:embed build/appicon.png
var iconData []byte

func main() {
	app := backend.NewApp()

	// 启动系统托盘（在 goroutine 中运行以防止阻塞主线程）
	go systray.Run(func() {
		systray.SetIcon(iconData)
		systray.SetTitle("Jietu OCR")
		systray.SetTooltip("Jietu OCR 截图翻译")

		mSettings := systray.AddMenuItem("偏好设置", "打开设置界面")
		mQuit := systray.AddMenuItem("退出程序", "彻底退出 Jietu OCR")

		mSettings.Click(func() {
			if app.Ctx != nil {
				runtime.EventsEmit(app.Ctx, "open_settings_from_tray")
			}
		})

		mQuit.Click(func() {
			systray.Quit()
			os.Exit(0)
		})
	}, func() {})

	err := wails.Run(&options.App{
		Title:  "Jietu OCR",
		Width:  60,
		Height: 60,
		MinWidth: 60,
		MinHeight: 60,
		Frameless: true,
		AlwaysOnTop: true,
		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		BackgroundColour: &options.RGBA{R: 0, G: 0, B: 0, A: 0},
		OnStartup:        app.Startup,
		OnShutdown:       app.Shutdown,
		Bind: []interface{}{
			app,
		},
		Linux: &linux.Options{
			WindowIsTranslucent: true,
			Icon: iconData,
		},
	})

	if err != nil {
		fmt.Println("Error:", err.Error())
	}
}
