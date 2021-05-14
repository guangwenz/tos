import sublime
import sublime_plugin
from string import Template
import datetime

def gen_order(expr, add_cancel=False):
    exp = [i.upper() for i in expr.split(" ") if i.strip()]
    ticker=exp[0]
    size=exp[1]

    time=""
    if add_cancel:
        cancel_at=(datetime.date.today() + datetime.timedelta(days=1)).strftime("%m/%d/%y") + " 6:40:00"
        time="CANCEL AT "+cancel_at

    if int(size) < 0:
        t=Template("SELL $count $ticker MKT WHEN $ticker STUDY 'open <= If(open[1]>close[1],close[1],open[1]) and close < low[1];D' IS TRUE")
    else:
        t=Template("BUY $count $ticker MKT $time WHEN $ticker STUDY 'open >= If(open[1]>close[1],open[1],close[1]);D' IS TRUE")
    return t.substitute(ticker=ticker, count=size, time=time)

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
    def run(self,edit):
        s = self.view.sel()
        for i in range(len(s)):            
            lr = self.view.line(s[i])
            data = self.view.substr(lr)
            exp = [i for i in data.split(" ") if i.strip()]
            
            if len(exp) == 2:
                content=gen_order(data)
                self.view.replace(edit, lr, content)
                sublime.set_clipboard(content)
                self.view.set_status("tos","Order copied to clipboard!")