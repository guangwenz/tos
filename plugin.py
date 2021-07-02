import sublime
import sublime_plugin
from string import Template
import datetime

def gen_order(expr, add_cancel_at=False, time_frame="D"):
    """
    Generate buy and sell orders

    Examples:
    TSLA 1 -> Buy TSLA With OpenInWick setup
    TSLA 1 700 -> Buy TSLA wiht OpenInWick and Stop price $700

    TSLA -1 -> Sell TSLA when it closes 3% below EMA 20
    TSLA -1 13 -> Sell TSLA OCO when it closes 3% below EMA 20 or 13% above its 10 week EMA
    TSLA -1 13 690 -> Sell TSLA OCO at stop loss price 690 or 13% above its 10 week EMA
    """
    exp = [i.upper() for i in expr.split(" ") if i.strip()]
    ticker=exp[0]
    size=exp[1]

    next_day = datetime.date.today()
    wd=next_day.isoweekday()
    if wd == 5:
        delta = 3
    elif wd == 6:
        delta = 2
    else:
        delta = 1
    next_day += datetime.timedelta(days=delta)
    order_time = " SUBMIT AT " + next_day.strftime("%m/%d/%y") + " 06:30:20"
    # order_time = ""
    cancel_time=""
    if add_cancel_at:
        order_time=order_time+" CANCEL AT "+next_day.strftime("%m/%d/%y") + " 06:36:00"

    if int(size) < 0:            
        if len(exp)==4:
            up=exp[2]
            stp=exp[3]
            return (
                f"SELL {size} {ticker} MKT GTC OCO WHEN {ticker} STUDY 'close >= ExpAverage(high, 10)*1.{up};W' IS TRUE\n"
                f"SELL {size} {ticker} STP {stp} GTC OCO"
                )
        elif len(exp)==3:
            up=exp[2]
            return (
                f"SELL {size} {ticker} MKT GTC OCO WHEN {ticker} STUDY 'close >= ExpAverage(high, 10)*1.{up};W' IS TRUE\n"
                f"SELL {size} {ticker} MKT GTC OCO WHEN {ticker} STUDY 'close < ExpAverage(close,20)*(1-0.03);{time_frame}' IS TRUE"
                )
        else:
            return f"SELL {size} {ticker} MKT GTC TRG BY OCO WHEN STUDY 'close < ExpAverage(close, 2)*(1-0.03);{time_frame}' IS TRUE"
        # t=Template("SELL $count $ticker MKT GTC WHEN $ticker STUDY 'close < expaverage(close,20)*(1-0.03);$time_frame' IS TRUE")
    else:
        oco=(
            # f"SELL -{size} {ticker} MKT GTC TRG BY OCO WHEN {ticker} STUDY 'close >= ExpAverage(high,10)*1.13;W' IS TRUE\n"
            f"SELL -{size} {ticker} STP TRG-2.00% GTC"
            )
        if len(exp)==3:
            stp=exp[2]
            return f"BUY {size} {ticker} STP {stp}{order_time} WHEN {ticker} STUDY 'open >= (Max(open[1],close[1]) * 0.9995);{time_frame}' IS TRUE\n{oco}"
        else:
            return f"BUY {size} {ticker} MKT{order_time} WHEN {ticker} STUDY 'open >= (Max(open[1],close[1]) * 0.9995);{time_frame}' IS TRUE\n{oco}"

'''
order input, samples:
`DE 1`, long position, use last day's open as wick base
`DE -1`, short position, use last day's open as wick base
'''
class MyOrderInput(sublime_plugin.TextInputHandler):
    def __init__(self, view):
        self.view = view

    def name(self):
        return "template"

    def placeholder(self):
        return "Expression"

    def initial_text(self):
        if len(self.view.sel()) == 1:
            return self.view.substr(self.view.sel()[0]).split("\n")[0]
        elif self.view.sel()[0].size() == 0:
            return ""
        else:
            return "bundle"

    def preview(self, expr):
        try:
            v = self.view
            s = v.sel()
            count = len(s)
            if count > 2:
                count = 2
            # results = [repr(gen_order(expr)) for i in range(count)]
            results=[]
            for i in range(count):
                si = s[i]
                data = v.substr(si).split("\n")[0]
                t = data if data else expr
                results.append(gen_order(t))
            if count != len(s):
                results.append("...")
            return "\n".join(results)
        except Exception:
            return ""

    def validate(self, expr):
        exp = [i for i in expr.split(" ") if i.strip()]
        return expr=='bundle' or len(exp) == 2 and exp[1].replace("+","").replace("-","").isdigit()

class MyOrderCommand(sublime_plugin.TextCommand):    
    def run(self, edit, template):
        for i in range(len(self.view.sel())):
            s = self.view.sel()[i]
            data = self.view.substr(s).split("\n")[0]
            
            t = data if data else template
            self.view.replace(edit, s, gen_order(t))

    def input(self, args):
        return MyOrderInput(self.view)

'''
Plugin to generate thinkorswim order template from current line, same as above but without input handler
'''
class AutoOrderCommand(sublime_plugin.TextCommand):
    def run(self,edit, add_cancel_at=False,time_frame="D"):
        s = self.view.sel()
        for i in range(len(s)):            
            lr = self.view.line(s[i])
            data = self.view.substr(lr)
            exp = [i for i in data.split(" ") if i.strip()]

            if len(exp) > 1:
                content=gen_order(data,add_cancel_at,time_frame)
                self.view.replace(edit, lr, content)
                sublime.set_clipboard(content)
                self.view.set_status("tos","Order copied to clipboard!")