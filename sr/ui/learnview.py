"""計算尺知識：原理、乘除、常見刻度、圓算尺與歷史（內容整理自需求文件附的維基百科「計算尺」條目）。"""
import flet as ft

from . import theme as T

I = ft.Icons

SOURCE = "內容整理自維基百科「計算尺」條目（創用 CC 姓名標示－相同方式分享 4.0）與 Infinirule 說明；圖片取自同條目。"

SECTIONS = [
    ("什麼是計算尺", "image1.jpg", "滑尺上的游標", [
        "計算尺，也叫對數計算尺或滑尺（英文 Slide rule），是一種類比計算工具。通常由三條互相鎖住、刻有刻度的長條，"
        "和一個可以滑動的窗口（游標）組成。一九七零年代以前，工程師和學生廣泛用它做計算，之後才被電子計算機取代。",
        "中間那一條叫滑尺，可以沿著長度方向滑動；外側兩條是固定的定尺。游標上的豎直細線（髮線）用來記錄中間結果，"
        "也能對齊不相鄰的刻度。"]),
    ("基本原理：對數把乘法變成加法", "image2.jpg", "用計算尺乘以 2：D 刻度上的每個數，都是上面 C 刻度的兩倍", [
        "計算尺最基本的兩個刻度是對數刻度：一個數字刻在離「1」（叫做索引）的距離和它的對數成正比的位置。",
        "因為 log(x×y) = log x + log y，把兩段長度接起來就等於相乘；反過來長度相減就是相除。"
        "計算尺只給出答案的有效數字，小數點的位置要使用者自己估算決定。"]),
    ("乘法", "image3.jpg", "上刻度的 1 對準下刻度的 2，上刻度的 3.5 對著下刻度的 7", [
        "把上面刻度的 1 對準下面刻度的 2，整個上刻度就向右移了 log 2 的距離。"
        "這時上刻度的每一個數（乘數）都對著下刻度上它和 2 的乘積：3.5 對 7、4 對 8……",
        "傳統直尺有時候會「超出範圍」，例如 2×7 的 7 已經跑到尺外，只好改用尺另一頭的 1，等於算 0.2×7＝1.4，"
        "再自己把答案調成 14。本系統的刻度會自動環繞，像圓形計算尺一樣，不會超出尺外。"]),
    ("除法", "image4.jpg", "5.5 ÷ 2：上面的 2 對準下面的 5.5，上面的 1 指著商 2.75", [
        "把上刻度的除數 2 對準下刻度的被除數 5.5，上刻度的 1 所對著的下刻度數字就是商 2.75。",
        "做除法的方式不只一種，可以選擇使用兩端任一個 1，這樣答案就不會跑出尺外。"]),
    ("其他刻度", "image5.jpg", "常見的刻度：A、B 平方；C、D 基本；K 立方；S、T 三角；L 對數", [
        "除了基本的對數刻度，很多計算尺還有其他函數刻度：A、B 是雙循環的平方刻度，K 是三循環的立方刻度，"
        "CI、DI 是由右往左的倒數刻度，CF、DF 是從 π 開始的摺疊刻度。",
        "S、T、ST 用來找正弦和正切；L 是線性刻度，配合 D 找常用對數；LL 是雙對數刻度，用來算自然對數與指數。",
        "在 A 刻度上求平方根要小心：A 有左右兩個 9，求 9 的平方根要用第一個 9，用第二個就變成 90 的平方根了。"]),
    ("雙面計算尺", "image6.jpg", "K&E 4081-3 計算尺的正面和反面", [
        "高級的雙面（雙工）計算尺在正反兩面都有刻度，常在背面重複一些刻度，方便連續計算。"
        "三角刻度有時用一黑一紅兩種標記，標出互補的角度，這就是所謂「Darmstadt（達姆施塔特）」風格。"]),
    ("圓算尺與柱狀算尺", "image7.jpg", "柱狀算尺", [
        "圓算尺把刻度刻成圓環，最長的尺寸縮小到大約三分之一（π 倍），而且刻度「環繞」，從不需要換另一頭的 1，"
        "這正是本系統自動環繞刻度的靈感來源。飛行員至今仍在使用的 E6B 航空計算尺，就是一種圓算尺。",
        "柱狀算尺把刻度做成螺旋或多段排列在圓柱上，能得到更長的刻度和更高的準確度，例如 Fuller 與 Otis King 算尺。"]),
    ("材料與保養", "image8.jpg", "Otis King Model K", [
        "傳統的計算尺用桃花心木、黃楊木或竹子製成；竹子尺寸穩定、堅固又自然潤滑，後來才改用塑膠或鋁。"
        "早期的游標是帶金屬框的玻璃，帶放大鏡的游標可以讓精度加倍。",
        "本系統的虛擬計算尺可以一直放大，精度不受材料限制：每放大十倍，讀數就多一位有效數字。"]),
    ("精度與讀數", "image9.jpg", "上海計算尺廠 1200 型向量自然對數計算尺", [
        "一般十英寸計算尺可以讀到兩位有效數字，再估計第三位。本系統下方的游標讀數會依放大倍率顯示合理的位數，"
        "放得越大，位數越多。",
        "練習時請像真的計算尺一樣：先用計算尺讀出有效數字，再用估算決定小數點的位置。"]),
]


class Learn(ft.Column):
    def __init__(self, ctx, **kw):
        self.ctx = ctx
        cards = []
        for i, (title, img, cap, paras) in enumerate(SECTIONS):
            text = ft.Column([ft.Text(p, size=15, color=T.TEXT, selectable=True) for p in paras], spacing=10,
                             expand=True)
            pic = ft.Column([ft.Image(src="learn/" + img, width=340, fit=ft.BoxFit.CONTAIN, border_radius=8),
                             T.muted(cap, 12)], spacing=4, width=340,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            cards.append(T.card(ft.Column([
                ft.Row([ft.Container(ft.Text(str(i + 1), color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
                                     width=30, height=30, border_radius=15, bgcolor=T.GOLD,
                                     alignment=ft.Alignment.CENTER),
                        T.title_text(title, 18), ft.Container(expand=True),
                        ft.IconButton(I.VOLUME_UP, tooltip="朗讀這一段",
                                      on_click=lambda e, t=title, p=paras: ctx.say_text(t + "。" + "".join(p)))],
                       spacing=10),
                ft.Row([text, pic], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START, data="split")],
                spacing=12), padding=20))
        super().__init__([T.page_header(I.MENU_BOOK, "計算尺知識", "原理、乘除、刻度、圓算尺與歷史", "violet",
                                        [T.btn("到計算尺試試看", I.STRAIGHTEN, lambda e: ctx.app.go("rule"))])]
                         + cards + [T.muted(SOURCE, 11)], spacing=14, expand=True, scroll=ft.ScrollMode.AUTO)
