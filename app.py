from encodings import utf_8
import os
from io import StringIO
import subprocess
from types import MethodType
import markdown
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
import proselint
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
from readtime import of_markdown
import tempfile
import nltk

app = Flask(__name__)
nltk.data.path = [str(pathlib.Path().absolute()) + "/nltk_data/"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/upload", methods=["POST"])
def upload():

    with open("/tmp/output_file", "bw") as f:
        chunk_size = 4096
        while True:
            chunk = request.stream.read(chunk_size)
            if len(chunk) == 0:
                return
            f.write(chunk)

@app.route('/vale_config', methods=['GET', 'POST'])
def loadValeConfig():
    filepath = 'valeconfig/vale.ini'
    with open(filepath, 'r') as f:
        content = f.read()
    if request.method == "GET":
        presentation = f'<form action = "/vale_config" method="POST"><div class="form-group">\
            <textarea id="valeconfig" spellcheck="false" name="valeconfig" rows="20" cols="80">{content}</textarea></div>\
            <button type="submit" class="btn btn-primary">Submit</button>\
            </form>'


        with open(filepath, 'r') as f:
            content = f.read()
        return render_template('vale_config.html', header1="Edit Vale Configuration", presentation=presentation)

    if request.method == "POST":
        content = request.form['valeconfig']
        with open(filepath, 'w') as f:
            f.write(content)
        with open(filepath, 'r') as f:
            content=f.read()
        presentation = f'<code><pre>{content}</pre></code>'
        return render_template('vale_config.html', header1="Vale Configuration", presentation=presentation)

@app.route('/md_config', methods=['GET', 'POST'])
def loadMdConfig():
    filepath = 'mdlintconfig/markdownlintconfig.json'
    with open(filepath, 'r') as f:
        content = f.read()
    if request.method == "GET":
        presentation = f'<form action = "/md_config" method="POST"><div class="form-group">\
            <textarea id="mdconfig" spellcheck="false" name="mdconfig" rows="20" cols="80">{content}</textarea></div>\
            <button type="submit" class="btn btn-primary">Submit</button>\
            </form>'


        
        return render_template('mdlint_config.html', header1="Edit Markdown Lint Configuration", presentation=presentation)

    if request.method == "POST":
        content = request.form['mdconfig']
        with open(filepath, 'w') as f:
            f.write(content)
        with open(filepath, 'r') as f:
            content=f.read()
        presentation = f'<code><pre>{content}</pre></code>'
        return render_template('vale_config.html', header1="Markdown Lint Configuration", presentation=presentation)

@app.route('/', methods=['POST'])
def upload_file():
    uploaded_file = request.files['md_file']
    source = str(uploaded_file.getvalue(), 'utf-8')
    file = StringIO(source)
    
    #lint = subprocess.run(['vale', '--ext=.md', '--config="vale/.vale.ini"', source], capture_output=True, text=True)
    #print(lint.stdout)
    temp = tempfile.NamedTemporaryFile(suffix='.md')
    temp.write(source.encode("utf-8"))


    
    
    #lint = subprocess.run(['vale', 'config="./.vale.ini"', source], capture_output=True, text=True)

    stats = getStats(source)       
    proselinted = proselint_annotate(source)
    #vale_feedback = vale_annotations(source)
    vale_feedback = vale_annotate(source)
    readability = vale_feedback[0]
    valelinted = vale_feedback[1]
    read_time = readtime_of_markdown(source)
    link_check = markdownlinkcheck(temp.name)
    print("beginning markdown lint")
    mdlint = markdownlint(temp.name)
    temp.close()
    markdown_source = transform_markdown(source)
    
    md_with_proselint = markdown.markdown(proselinted, extensions=['md_in_html', 'mdx_truly_sane_lists', 'fenced_code', 'extra', 'toc', 'pymdownx.superfences', 'pymdownx.highlight'], output_format="html5") 
    md_with_vale = markdown.markdown(valelinted, extensions=['md_in_html', 'mdx_truly_sane_lists', 'fenced_code', 'extra', 'toc', 'pymdownx.superfences', 'pymdownx.highlight'], output_format="html5") 
    try:
        return render_template('xray.html', readability=readability, proselint=md_with_proselint, read_time=read_time, vale=md_with_vale, md=markdown_source, linkcheck=link_check, mdlint=mdlint, stats=stats)
    except:
        return render_template('xray.html', readability=readability, proselint=md_with_proselint, read_time=read_time, vale=md_with_vale, md=markdown_source, linkcheck=link_check, mdlint=None, stats=stats)
    #return render_template('xray.html', proselint=md_with_proselint, read_time=read_time)
    #return jsonify(valelinted)
    #uploaded_file = request.files['md_file']
    #if uploaded_file.filename != '':
    #    uploaded_file.save(uploaded_file.filename)
    #    with open(uploaded_file.filename, 'r') as f:
    #        source = f.read()
        # md = markdown.markdown(source, extensions=['mdx_truly_sane_lists', 'fenced_code', 'extra', 'toc', 'smarty', 'pymdownx.superfences', 'pymdownx.highlight'], output_format="html5") 
    #return render_template('xray.html', content=md)
    

def proselinter(input):
    errors = json.loads(proselint.tools.errors_to_json(proselint.tools.lint(input, config_file_path='./proselintconfig/config.json')))
    #print(errors)
    return errors

def proselint_annotate(source):
    proselint_errors = proselinter(source)
    lines = source.split('\n')
    for lint in proselint_errors['data']['errors']:
        m = str(lint['message'])
        s = lint['severity']
        lines = source.split('\n')
        original = lines[int(lint['line'])-1][int(lint['column'])-1:int(lint['end']-1)]
        if s == "warning":
            c = "#8B8000"
        else:
            c = "red"
        #lines[int(lint['line'])-1] = lines[int(lint['line'])-1].replace(str(original), f'<span style="color:{c}" title="{m}">{original}</span>')
        
    #out = '\n'.join(lines)
    
        lines[int(lint['line'])-1] = lines[int(lint['line'])-1].replace(str(original), f'<bold><a href="#" style="color:{c}; text-decoration: red wavy underline;" data-toggle="tooltip" title="{m}">{original}</a></bold>')
        #print(lines[int(lint['line'])-1])
    out = '\n'.join(lines)
    return out    

def valelinter(input):
    valeconfig = "valeconfig/vale.ini"
    errors = subprocess.run(['/snap/bin/vale', "--ext=.md", "--output=JSON", "--config=" + valeconfig, input], capture_output=True, text=True)
    if errors.stdout:
        errors = json.loads(errors.stdout)['stdin.md']
        return errors
    else:
        return ""
def vale_annotate(source):
    vale_errors = valelinter(source)
    readability = []
    lines = source.split("\n")
    for check in vale_errors:
        if "Readability" in check['Check']:
            readability.append(f"<a href='{check['Link']}'>{check['Check']}</a>: {check['Message']}")
            
        if check['Severity'] == "suggestion":
            vale_errors.remove(check)
    for check in vale_errors:
        m = check['Message']
        sev = check['Severity']
        line = check['Line']
        start = check['Span'][0]
        end = check['Span'][1]
        
        original = lines[int(line)-1]
        if sev == "warning":
            c = "warning"
        elif sev == "suggestion":
            c = "primary"
        else:
            c = "danger"
        rule = check['Check'].split(".")
        
        if ">" in m:
            m = m.replace(">", "&gt;")
        elif "<" in m:
            m = m.replace("<", "&lt;")
        else:
            pass
        #print(line, sev, m, sep="|")
        if ("Readability" in check['Check']) or ("![" in original and "(" in original):
            pass
        else:
            #       <a type="button" class="btn" href="#" data-toggle="popover" title="Popover Header" data-content="Some content inside the popover">Toggle popover</a>

            lines[int(line)-1] = lines[int(line)-1].replace(original, f'{original} &nbsp; <a type="button" class="btn btn-sm btn-{c}" style="padding: .05rem .25rem;font-size:8pt" data-placement="bottom" data-trigger="hover" data-toggle="popover" title="{rule[0]}: {rule[1]}" data-content="{m}">{rule[1]}</a>')
    #out = '\n'.join(lines)
    #out = "No Feedback"
    #return readability, out
    #return errors
    out = '\n'.join(lines)
    return readability, out
def vale(source):
    valeconfig = "valeconfig/vale.ini"
    errors = subprocess.run(['/snap/bin/vale', "--ext=.md", "--output=JSON", "--config=" + valeconfig, source], capture_output=True, text=True)
    errors = json.loads(errors.stdout)['stdin.md']
    for check in errors:
        line = check["Line"]
        start = check["Span"][0]
        end = check["Span"][1]
        severity = check["Severity"]
        message = check["Message"]
            

def readtime_of_markdown(source):
    return of_markdown(source)

def transform_markdown(source):


    from pygments import highlight
    from pygments.lexers.markup import MarkdownLexer
    from pygments.formatters import HtmlFormatter
    
    
    lexer = MarkdownLexer()
    formatter = HtmlFormatter(cssclass="markdown")
    
    return highlight(source, lexer, formatter)

    
    
    
    #source = source.replace("<", "&lt;").replace(">", "&gt;")
    #return source
    
def markdownlinkcheck(path):
    
    result = subprocess.run(['/home/rik/.npm-packages/bin/markdown-link-check', path], capture_output=True, text=True)
    if result.stdout:
        import re
        import urllib.parse
        from markupsafe import Markup
        regex = re.compile(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", re.IGNORECASE)
        out = []
        lines = result.stdout.split("\n")
        for line in lines:
            match = re.search(regex, line)
            if match:
                url = match.group()
                #print(url)
                #url = url.replace("%7D", "").replace("%5B", "").replace("%5D", "")
                if "???" in line:
                    line = line.replace(url, '<a style=\"color:red;\" target=\"_blank\" href=\"' + url + ' \"/>' + url + '</a>').replace("???", "<span style='color:red'>???</span>")
                else:
                    line = line.replace(url, '<a target=\"_blank\" href=\"' + url + ' \"/>' + url + '</a>').replace("???", '<span style="color:green">???</span>')
                
                out.append(Markup(line))    
            elif "FILE:" in line:
                pass
            else:
                out.append(Markup(line))
        
        return out
    else:
        return "No Results"

def markdownlint(path):
    result = subprocess.run(['markdownlint', '--config=./mdlintconfig/markdownlintconfig.json', '--json', path], capture_output=True, text=True)
    if result.stderr:
        result = json.loads(result.stderr)
      
        with open(path, 'r') as f:
            source = f.readlines()

        for lint in result:
            ruleCode = lint["ruleNames"][0] 
            ruleName = lint['ruleNames'][1]
            ruleDescription = lint['ruleDescription']
            url = lint['ruleInformation']
            line = lint['lineNumber']
            errorContext = lint['errorContext']
            errorRange = lint['errorRange']
            try:
                segment = source[line-1][errorRange[0]-1:errorRange[1]-1]
            except:
                segment = None
                #source[line-1] = source[line-1][errorRange[0]:errorRange[1]].replace(source[line-1][errorRange[0]-1:errorRange[1]-1], (f'<a href="{url}" title="{ruleDescription}">{source[line-1][errorRange[0]-1:errorRange[1]-1]}</a>\n'))
            
            
            if segment:
                source[line-1] = source[line-1].replace(segment, (f'<a data-placement="bottom" data-trigger="hover" data-toggle="popover" style="text-decoration:red wavy underline;" title="{ruleCode}:{ruleDescription}" data-content="Line {line}\n Context: {errorContext}">{segment}</a>'))
            elif ruleDescription == "Trailing spaces":
                source[line-1] = source[line-1] + f'<a data-placement="bottom" data-trigger="hover" data-toggle="popover" style="color:red;text-decoration:red wavy underline;" title="{ruleCode}:{ruleDescription}" data-content="Line {line}\n Context: {errorContext}">&#128997;</a>'
            else:
                source[line-1] = source[line-1] + f'<span title="{ruleCode}:{ruleDescription}" data-content="Line {line}\n Context: {errorContext}" data-placement="bottom" data-trigger="hover" data-toggle="popover" class="badge badge-danger">{ruleDescription}</span>' 


            
        return source

def getStats(md):
    from bs4 import BeautifulSoup
    from passive.passive import main as passive
    from readability import getmeasures as readability
    html = markdown.markdown(md)
    soup = BeautifulSoup(html, features='html.parser')
    text = soup.get_text()
    result = readability(text, lang='en')
    return (round(float(100 * (len(passive(text))/result['sentence info']['sentences'])), 0)), round(result['word usage']['tobeverb']/result['sentence info']['sentences'],2)
    


if __name__ == '__main__':
   app.run(debug = True)
