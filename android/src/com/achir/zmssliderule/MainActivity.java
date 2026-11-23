package com.achir.zmssliderule;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.res.AssetFileDescriptor;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.webkit.ConsoleMessage;
import android.webkit.JsResult;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 資料助秘計算尺 — Android 版
 * 用 WebView 開啟和線上版同一份網頁（放在 APK 的 assets/web）→ 不用網路也能用。
 * 網頁從 https://appassets.androidplatform.net/ 載入（安全來源，localStorage 才能保存成績），
 * 由 shouldInterceptRequest 直接回傳 assets 裡的檔案；語音 MP3 支援 Range。
 * 離開 App 時 WebView 一併銷毀：示範、語音全部停止。
 */
public class MainActivity extends Activity {
    static final String TAG = "ZMSSlideRule";
    static final String ORIGIN = "https://appassets.androidplatform.net";
    static final Pattern RANGE = Pattern.compile("bytes=(\\d*)-(\\d*)");

    WebView web;
    Bridge bridge;
    long lastBack = 0;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        web = new WebView(this);
        web.setBackgroundColor(0xFFEEF2F7);
        setContentView(web);
        WebView.setWebContentsDebuggingEnabled(BuildFlags.DEBUG);   // python android/build.py debug 才開（chrome://inspect）

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);   // 語音示範一步接一步自動播放
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setSupportZoom(false);
        s.setTextZoom(100);   // 不跟著系統字型大小放大，計算尺與按鈕才不會擠在一起
        s.setUserAgentString(s.getUserAgentString() + " ZMSSlideRuleAndroid/" + Bridge.version(this));

        bridge = new Bridge(this);
        web.addJavascriptInterface(bridge, "ZMSAndroid");
        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest req) {
                Uri u = req.getUrl();
                if (!ORIGIN.equals(u.getScheme() + "://" + u.getHost())) return null;
                return serve(u.getPath(), req.getRequestHeaders());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest req) {
                Uri u = req.getUrl();
                if (ORIGIN.equals(u.getScheme() + "://" + u.getHost())) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, u).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); } catch (Exception ignored) { }
                return true;
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage m) {
                Log.d(TAG, m.message() + " @" + m.sourceId() + ":" + m.lineNumber());
                return true;
            }

            // 網頁的 confirm()（清除紀錄、刪除尺型、更新）用中文按鈕的對話框
            @Override
            public boolean onJsConfirm(WebView v, String url, String msg, final JsResult r) {
                new AlertDialog.Builder(MainActivity.this).setMessage(msg)
                        .setPositiveButton("確定", (d, w) -> r.confirm())
                        .setNegativeButton("取消", (d, w) -> r.cancel())
                        .setOnCancelListener(d -> r.cancel()).show();
                return true;
            }

            @Override
            public boolean onJsAlert(WebView v, String url, String msg, final JsResult r) {
                new AlertDialog.Builder(MainActivity.this).setMessage(msg)
                        .setPositiveButton("確定", (d, w) -> r.confirm())
                        .setOnCancelListener(d -> r.confirm()).show();
                return true;
            }
        });

        web.loadUrl(ORIGIN + "/app/index.html");
    }

    /** 回傳 assets/web 裡的檔案（語音 MP3 支援 Range） */
    WebResourceResponse serve(String path, Map<String, String> reqHeaders) {
        try {
            if (path == null || path.isEmpty()) path = "/";
            if (path.endsWith("/")) path += "index.html";
            String asset = "web" + Uri.decode(path);
            String m = mime(path);
            Map<String, String> h = new HashMap<>();
            h.put("Cache-Control", "no-store");
            h.put("Access-Control-Allow-Origin", ORIGIN);
            String range = null;
            if (reqHeaders != null) for (Map.Entry<String, String> e : reqHeaders.entrySet()) if ("range".equalsIgnoreCase(e.getKey())) range = e.getValue();
            if (m.startsWith("audio/")) {
                AssetFileDescriptor fd = getAssets().openFd(asset);   // mp3 以不壓縮方式打包，才能取得長度
                long len = fd.getLength();
                fd.close();
                h.put("Accept-Ranges", "bytes");
                if (range != null) {
                    Matcher rm = RANGE.matcher(range);
                    if (rm.find()) {
                        long start = rm.group(1).isEmpty() ? 0 : Long.parseLong(rm.group(1));
                        long end = rm.group(2).isEmpty() ? len - 1 : Math.min(len - 1, Long.parseLong(rm.group(2)));
                        InputStream in = getAssets().open(asset);
                        long skipped = 0;
                        while (skipped < start) { long k = in.skip(start - skipped); if (k <= 0) break; skipped += k; }
                        h.put("Content-Range", "bytes " + start + "-" + end + "/" + len);
                        h.put("Content-Length", String.valueOf(end - start + 1));
                        return new WebResourceResponse(m, null, 206, "Partial Content", h, new Limited(in, end - start + 1));
                    }
                }
                h.put("Content-Length", String.valueOf(len));
                return new WebResourceResponse(m, null, 200, "OK", h, getAssets().open(asset));
            }
            InputStream in = getAssets().open(asset);
            return new WebResourceResponse(m, m.startsWith("text") || m.endsWith("json") ? "utf-8" : null, 200, "OK", h, in);
        } catch (Exception e) {
            return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", null, null);
        }
    }

    /** 只讀固定長度的串流（Range 用） */
    static final class Limited extends java.io.FilterInputStream {
        long left;
        Limited(InputStream in, long n) { super(in); left = n; }
        @Override public int read() throws java.io.IOException { if (left <= 0) return -1; int c = super.read(); if (c >= 0) left--; return c; }
        @Override public int read(byte[] b, int off, int len) throws java.io.IOException {
            if (left <= 0) return -1;
            int n = super.read(b, off, (int) Math.min(len, left));
            if (n > 0) left -= n;
            return n;
        }
    }

    static String mime(String p) {
        p = p.toLowerCase();
        if (p.endsWith(".html")) return "text/html";
        if (p.endsWith(".js")) return "text/javascript";
        if (p.endsWith(".css")) return "text/css";
        if (p.endsWith(".json") || p.endsWith(".webmanifest")) return "application/json";
        if (p.endsWith(".png")) return "image/png";
        if (p.endsWith(".jpg") || p.endsWith(".jpeg")) return "image/jpeg";
        if (p.endsWith(".mp3")) return "audio/mpeg";
        return "application/octet-stream";
    }

    /** 返回鍵：不在計算尺分頁就回到計算尺；在計算尺分頁按兩次才離開 */
    @Override
    public void onBackPressed() {
        web.evaluateJavascript("(function(){try{return !!(window.__zmsBack&&window.__zmsBack())}catch(e){return false}})()", v -> {
            if ("true".equals(v)) return;
            long now = System.currentTimeMillis();
            if (now - lastBack < 2000) { finish(); return; }
            lastBack = now;
            Toast.makeText(this, "再按一次返回鍵離開", Toast.LENGTH_SHORT).show();
        });
    }

    /** 給 Bridge 用：在網頁執行 JavaScript */
    void js(final String code) {
        runOnUiThread(() -> { if (web != null) web.evaluateJavascript(code, null); });
    }

    @Override
    protected void onPause() { super.onPause(); web.onPause(); bridge.ttsStop(); }

    @Override
    protected void onResume() { super.onResume(); web.onResume(); }

    @Override
    protected void onDestroy() {
        bridge.shutdown();
        web.removeJavascriptInterface("ZMSAndroid");
        web.loadUrl("about:blank");
        web.destroy();
        web = null;
        super.onDestroy();
    }
}
