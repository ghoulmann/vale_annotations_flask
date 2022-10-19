import os
from io import StringIO
import subprocess
import markdown
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
import proselint
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
from readtime import of_markdown
app = Flask(__name__)

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
@app.route('/', methods=['POST'])
def upload_file():
    uploaded_file = request.files['md_file']
    source = str(uploaded_file.getvalue(), 'utf-8')
    file = StringIO(source)
    
    #lint = subprocess.run(['vale', '--ext=.md', '--config="vale/.vale.ini"', source], capture_output=True, text=True)
    #print(lint.stdout)
    
    
    #lint = subprocess.run(['vale', 'config="./.vale.ini"', source], capture_output=True, text=True)


    proselinted = proselint_annotate(source)
    #vale_feedback = vale_annotations(source)
    vale_feedback = vale_annotate(source)
    readability = vale_feedback[0]
    valelinted = vale_feedback[1]
    read_time = readtime_of_markdown(source)
    markdown_source = transform_markdown(source)
    md_with_proselint = markdown.markdown(proselinted, extensions=['md_in_html', 'mdx_truly_sane_lists', 'fenced_code', 'extra', 'toc', 'pymdownx.superfences', 'pymdownx.highlight'], output_format="html5") 
    md_with_vale = markdown.markdown(valelinted, extensions=['md_in_html', 'mdx_truly_sane_lists', 'fenced_code', 'extra', 'toc', 'pymdownx.superfences', 'pymdownx.highlight'], output_format="html5") 
    #lintmarkdown(source)
    return render_template('layout.html', readability=readability, proselint=md_with_proselint, read_time=read_time, vale=md_with_vale, md=markdown_source)
    #return render_template('layout.html', proselint=md_with_proselint, read_time=read_time)
    #return jsonify(valelinted)
    #uploaded_file = request.files['md_file']
    #if uploaded_file.filename != '':
    #    uploaded_file.save(uploaded_file.filename)
    #    with open(uploaded_file.filename, 'r') as f:
    #        source = f.read()
        # md = markdown.markdown(source, extensions=['mdx_truly_sane_lists', 'fenced_code', 'extra', 'toc', 'smarty', 'pymdownx.superfences', 'pymdownx.highlight'], output_format="html5") 
    #return render_template('layout.html', content=md)
    

def proselinter(input):
    errors = json.loads(proselint.tools.errors_to_json(proselint.tools.lint(input, config_file_path='./proselintconfig/config.json')))
    print(errors)
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
        print(lines[int(lint['line'])-1])
    out = '\n'.join(lines)
    return out    

def valelinter(input):
    valeconfig = "valeconfig/vale.ini"
    errors = subprocess.run(['/snap/bin/vale', "--ext=.md", "--output=JSON", "--config=" + valeconfig, input], capture_output=True, text=True)
    errors = json.loads(errors.stdout)['stdin.md']
    return errors
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
            c = "info"
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
            lines[int(line)-1] = lines[int(line)-1].replace(original, f'{original} &nbsp; <span style="font-size:8pt" class="badge badge-{c} btn-sm" data-placement="top" data-trigger="hover" data-toggle="tooltip" title="{rule[0]}.{rule[1]}: {m} ({start}-{end})">{rule[1]}</span>')
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
        print(f"line: {line}|start: {start}|end: {end}|severity: {severity}|message: {message}")       

def readtime_of_markdown(source):
    return of_markdown(source)

def transform_markdown(source):


    from pygments import highlight
    from pygments.lexers.markup import MarkdownLexer
    from pygments.formatters import HtmlFormatter
    lexer = MarkdownLexer()
    formatter = HtmlFormatter(linenos=False, cssclass="source")
    result = highlight(source, lexer, formatter)
    print(result)
    return result

    
    #source = source.replace("<", "&lt;").replace(">", "&gt;")
    return source

#def lintmarkdown(source):
#    from pymarkdown import PyMarkdownLint
    
    

if __name__ == '__main__':
   app.run(debug = True)
