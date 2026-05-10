package backend

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"time"

	"github.com/otiai10/gosseract/v2"
)

type App struct {
	Ctx context.Context
}

func NewApp() *App {
	return &App{}
}

func (a *App) Startup(ctx context.Context) {
	a.Ctx = ctx
}

func (a *App) Shutdown(ctx context.Context) {
	// 纯 Go 版本不需要管理外部后台进程
}

func (a *App) getConfigPath() string {
	home, _ := os.UserHomeDir()
	configDir := filepath.Join(home, ".config", "jietu")
	os.MkdirAll(configDir, 0755)
	return filepath.Join(configDir, "config.json")
}

// 永久保存配置到本地文件
func (a *App) SaveConfig(configJSON string) error {
	return os.WriteFile(a.getConfigPath(), []byte(configJSON), 0644)
}

// 从本地文件加载配置
func (a *App) LoadConfig() string {
	data, err := os.ReadFile(a.getConfigPath())
	if err != nil {
		return "{}"
	}
	return string(data)
}

// 捕获屏幕区域 (调用 scrot -s)
func (a *App) CaptureSelection() (string, error) {
	tmpFile := "/tmp/jietu_capture.png"
	os.Remove(tmpFile)

	cmd := exec.Command("scrot", "-s", tmpFile)
	err := cmd.Run()
	if err != nil {
		return "", fmt.Errorf("截图失败或被取消: %v", err)
	}

	if _, err := os.Stat(tmpFile); os.IsNotExist(err) {
		return "", fmt.Errorf("未生成截图文件")
	}

	return tmpFile, nil
}

// 识别截图中的文字 (使用原生 Go 的 gosseract 库)
func (a *App) RecognizeText(imagePath string, lang string) (string, error) {
	client := gosseract.NewClient()
	defer client.Close()

	if lang == "" {
		lang = "eng" // 默认语言
	}

	client.SetImage(imagePath)
	client.SetLanguage(lang)

	text, err := client.Text()
	if err != nil {
		return "", fmt.Errorf("OCR 识别失败: %v", err)
	}

	return text, nil
}

// OpenAI 兼容的 AI 翻译服务
func (a *App) TranslateWithOpenAI(text, srcLang, targetLang, apiKey, endpoint, model string) (string, error) {
	if endpoint == "" {
		endpoint = "https://api.openai.com/v1/chat/completions"
	}
	if model == "" {
		model = "gpt-3.5-turbo"
	}

	// 构造清晰的翻译 Prompt
	systemPrompt := fmt.Sprintf("You are a professional translator. Translate the following text from %s to %s. Provide ONLY the translated text without any explanations or additional formatting.", srcLang, targetLang)

	reqBody := map[string]interface{}{
		"model": model,
		"messages": []map[string]string{
			{"role": "system", "content": systemPrompt},
			{"role": "user", "content": text},
		},
		"temperature": 0.3,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("构建 AI 请求失败: %v", err)
	}

	req, err := http.NewRequest("POST", endpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("创建 AI 请求失败: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+apiKey)
	}

	client := &http.Client{
		Timeout: 15 * time.Second,
	}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("调用 AI 接口失败: %v", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("读取 AI 返回失败: %v", err)
	}

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("AI 服务报错 (状态码 %d): %s", resp.StatusCode, string(body))
	}

	var res map[string]interface{}
	if err := json.Unmarshal(body, &res); err != nil {
		return "", fmt.Errorf("解析 AI JSON 失败: %v", err)
	}

	if choices, ok := res["choices"].([]interface{}); ok && len(choices) > 0 {
		if choice, ok := choices[0].(map[string]interface{}); ok {
			if message, ok := choice["message"].(map[string]interface{}); ok {
				if content, ok := message["content"].(string); ok {
					return content, nil
				}
			}
		}
	}

	return "", fmt.Errorf("AI 返回格式异常: %s", string(body))
}

// 综合入口：调用翻译接口
func (a *App) TranslateText(text string, srcLang string, targetLang string, service string, apiKey string, endpoint string, model string) (string, error) {
	if srcLang == "auto" || srcLang == "" {
		srcLang = "auto"
	}
	if targetLang == "" {
		targetLang = "zh-CN"
	}

	// 如果选择了 OpenAI 兼容的大模型
	if service == "OpenAI" {
		return a.TranslateWithOpenAI(text, srcLang, targetLang, apiKey, endpoint, model)
	}

	// 默认使用 Google 免费接口
	apiURL := fmt.Sprintf("https://translate.googleapis.com/translate_a/single?client=gtx&sl=%s&tl=%s&dt=t&q=%s",
		srcLang, targetLang, url.QueryEscape(text))

	client := &http.Client{
		Timeout: 10 * time.Second,
	}
	resp, err := client.Get(apiURL)
	if err != nil {
		return "", fmt.Errorf("翻译请求失败: %v", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("读取翻译结果失败: %v", err)
	}

	var result []interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return "", fmt.Errorf("解析翻译结果失败: %v", err)
	}

	if len(result) > 0 {
		innerList, ok := result[0].([]interface{})
		if ok {
			var fullTranslation string
			for _, item := range innerList {
				lineItem, ok := item.([]interface{})
				if ok && len(lineItem) > 0 {
					translatedLine, ok := lineItem[0].(string)
					if ok {
						fullTranslation += translatedLine
					}
				}
			}
			if fullTranslation != "" {
				return fullTranslation, nil
			}
		}
	}

	return "", fmt.Errorf("未找到翻译内容")
}
