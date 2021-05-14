import sublime
import sublime_plugin
from string import Template

def gen_order(expr):
    exp = [i.upper() for i in expr.split(" ") if i.strip()]
    ticker=exp[0]
    size=exp[1]

    if int(size) < 0:
        t=Template("SELL $count $ticker MKT WHEN $ticker STUDY 'open <= If(open[1]>close[1],close[1],open[1]) and close < low[1];D' IS TRUE")
    else:
        t=Template("BUY $count $ticker MKT WHEN $ticker STUDY 'open >= If(open[1]>close[1],open[1],close[1]);D' IS TRUE")
    return t.substitute(ticker=ticker, count=size)

'''
order input, samples:
`DE 1 o`, long position, use last day's open as wick base
`DE 1 c`, long position, use last day's close as wick base
`DE -1 o`, short position, use last day's open as wick base
`DE -1 c`, short position, use last day's close as wick base
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
            results = [repr(gen_order(expr)) for i in range(count)]
            if count != len(s):
                results.append("...")
            return ", ".join(results)
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
