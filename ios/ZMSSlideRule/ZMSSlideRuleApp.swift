import AVFoundation
import SwiftUI
import UIKit
import WebKit

/// 資料助秘計算尺 — iPhone／iPad 版
/// WKWebView 開啟 App 內建的計算尺網頁（和線上版同一份程式），由 LocalServer 在 127.0.0.1 提供 → 不用網路也能用。
/// 直放、橫放都可以；App 被關掉時網頁一起結束（示範、語音全部停止）。
@main
struct ZMSSlideRuleApp: App {
    init() {
        LocalServer.shared.start()
        // 語音示範：靜音開關打開時也要聽得到（和有聲書、教學影片一樣）
        try? AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
        try? AVAudioSession.sharedInstance().setActive(true)
    }

    var body: some Scene {
        WindowGroup {
            WebContainer()
                .background(Color(red: 0.059, green: 0.235, blue: 0.431))
                .ignoresSafeArea()
        }
    }
}

struct WebContainer: UIViewRepresentable {
    func makeUIView(context: Context) -> WKWebView { Web.shared.view }
    func updateUIView(_ v: WKWebView, context: Context) {}
}

/// 網頁與 App 之間的橋：網頁呼叫 window.webkit.messageHandlers.zms.postMessage({cmd, args})，回傳 Promise
final class Web: NSObject, WKScriptMessageHandlerWithReply, WKNavigationDelegate, WKUIDelegate {
    static let shared = Web()
    let view: WKWebView

    override init() {
        let cfg = WKWebViewConfiguration()
        cfg.allowsInlineMediaPlayback = true
        cfg.mediaTypesRequiringUserActionForPlayback = []      // 語音示範一步接一步自動播放
        cfg.websiteDataStore = .default()
        let ver = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "0"
        // 讓網頁知道自己在 iPhone／iPad App 裡（app.js 會改用 App 的檢查更新、開網址）；
        // 網頁的錯誤訊息轉到 iOS 系統記錄（除錯：log show --predicate 'process == "ZMSSlideRule"'）
        let shim = WKUserScript(source: """
            window.ZMSIOS = { version: '\(ver)' };
            (function () {
              function send(k, a) { try { window.webkit.messageHandlers.zms.postMessage({ cmd: 'log', args: [k, Array.prototype.map.call(a, function (x) { return x && x.stack ? x.stack : String(x); }).join(' ')] }); } catch (e) {} }
              var ce = console.error.bind(console);
              console.error = function () { send('error', arguments); ce.apply(null, arguments); };
              window.addEventListener('error', function (e) { send('pageerror', [e.message + ' @' + e.filename + ':' + e.lineno]); });
              window.addEventListener('unhandledrejection', function (e) { send('rejection', [e.reason]); });
            })();
            """, injectionTime: .atDocumentStart, forMainFrameOnly: true)
        cfg.userContentController.addUserScript(shim)
        view = WKWebView(frame: .zero, configuration: cfg)
        super.init()
        cfg.userContentController.addScriptMessageHandler(self, contentWorld: .page, name: "zms")
        view.navigationDelegate = self
        view.uiDelegate = self
        view.isOpaque = false
        view.backgroundColor = UIColor(red: 0.933, green: 0.949, blue: 0.969, alpha: 1)
        view.scrollView.backgroundColor = view.backgroundColor
        view.scrollView.bounces = false
        view.scrollView.contentInsetAdjustmentBehavior = .never   // 安全區域由網頁的 env(safe-area-inset-*) 處理
        view.allowsBackForwardNavigationGestures = false
        if #available(iOS 16.4, *) { view.isInspectable = true }
        view.load(URLRequest(url: LocalServer.shared.url))
    }

    // 外部連結（GitHub、安裝頁）用 Safari 開
    func webView(_ w: WKWebView, decidePolicyFor a: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if let u = a.request.url, u.host != "127.0.0.1", ["http", "https", "itms-services"].contains(u.scheme ?? ""), a.targetFrame?.isMainFrame != false {
            UIApplication.shared.open(u); decisionHandler(.cancel); return
        }
        decisionHandler(.allow)
    }
    func webView(_ w: WKWebView, createWebViewWith c: WKWebViewConfiguration, for a: WKNavigationAction, windowFeatures f: WKWindowFeatures) -> WKWebView? {
        if let u = a.request.url { UIApplication.shared.open(u) }
        return nil
    }

    // 網頁的 confirm()（清除紀錄、刪除尺型）：WKWebView 預設不顯示，要自己做對話框
    func webView(_ w: WKWebView, runJavaScriptConfirmPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let ac = UIAlertController(title: nil, message: m, preferredStyle: .alert)
        ac.addAction(UIAlertAction(title: "取消", style: .cancel) { _ in completionHandler(false) })
        ac.addAction(UIAlertAction(title: "確定", style: .default) { _ in completionHandler(true) })
        present(ac) { completionHandler(false) }
    }
    func webView(_ w: WKWebView, runJavaScriptAlertPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let ac = UIAlertController(title: nil, message: m, preferredStyle: .alert)
        ac.addAction(UIAlertAction(title: "確定", style: .default) { _ in completionHandler() })
        present(ac) { completionHandler() }
    }

    // 網頁被系統回收時（記憶體不足）自動重新載入
    func webViewWebContentProcessDidTerminate(_ w: WKWebView) { w.reload() }

    // MARK: 網頁呼叫的功能
    func userContentController(_ u: WKUserContentController, didReceive m: WKScriptMessage, replyHandler: @escaping (Any?, String?) -> Void) {
        guard let body = m.body as? [String: Any], let cmd = body["cmd"] as? String else { replyHandler(nil, "bad message"); return }
        let args = body["args"] as? [Any] ?? []
        let s = { (i: Int) -> String in args.count > i ? "\(args[i])" : "" }
        let ver = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "0"
        switch cmd {
        case "app_info":
            replyHandler(["status": "ok", "name": "資料助秘計算尺", "version": ver, "platform": "ios", "model": UIDevice.current.model], nil)
        case "log":
            NSLog("[web %@] %@", s(0), s(1))
            replyHandler(true, nil)
        case "open_url":
            if let u = URL(string: s(0)), ["github.com", "achir1015.github.io"].contains(u.host ?? "") { UIApplication.shared.open(u) }
            replyHandler(true, nil)
        default:
            replyHandler(nil, "unknown command \(cmd)")
        }
    }

    private func present(_ vc: UIViewController, fail: () -> Void) {
        let scene = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first
        var top = scene?.windows.first(where: { $0.isKeyWindow })?.rootViewController
        while let p = top?.presentedViewController { top = p }
        if let top { top.present(vc, animated: true) } else { fail() }
    }
}
