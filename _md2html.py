# -*- coding: utf-8 -*-
import re, sys, html as htmllib
SRC, HTML_OUT = sys.argv[1], sys.argv[2]
def parse_blocks(lines):
    blocks=[]; i=0; n=len(lines)
    while i<n:
        s=lines[i].rstrip('\n').strip()
        if s=='': i+=1; continue
        if s.startswith('```'):
            i+=1; buff=[]
            while i<n and not lines[i].strip().startswith('```'): buff.append(lines[i].rstrip('\n')); i+=1
            i+=1; blocks.append(('code','\n'.join(buff))); continue
        if s=='---': blocks.append(('hr',None)); i+=1; continue
        if s.startswith('### '): blocks.append(('h3',s[4:])); i+=1; continue
        if s.startswith('## '): blocks.append(('h2',s[3:])); i+=1; continue
        if s.startswith('# '): blocks.append(('h1',s[2:])); i+=1; continue
        if s.startswith('>'):
            buff=[]
            while i<n and lines[i].strip().startswith('>'): buff.append(lines[i].strip()[1:].strip()); i+=1
            blocks.append(('quote',' '.join(buff))); continue
        if s.startswith('|') and i+1<n and set(lines[i+1].strip())<=set('|-: '):
            header=[c.strip() for c in s.strip('|').split('|')]; i+=2; rows=[]
            while i<n and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i+=1
            blocks.append(('table',(header,rows))); continue
        if s.startswith('- '):
            items=[]
            while i<n and lines[i].strip().startswith('- '): items.append(lines[i].strip()[2:]); i+=1
            blocks.append(('ul',items)); continue
        if re.match(r'^\d+\.\s',s):
            items=[]
            while i<n and re.match(r'^\d+\.\s',lines[i].strip()): items.append(re.sub(r'^\d+\.\s','',lines[i].strip())); i+=1
            blocks.append(('ol',items)); continue
        blocks.append(('p',s)); i+=1
    return blocks
TOKEN_RE=re.compile(r'(\*\*.+?\*\*|`.+?`|\[.+?\]\(.+?\))')
def tokenize(text):
    out=[]; pos=0
    for m in TOKEN_RE.finditer(text):
        if m.start()>pos: out.append((text[pos:m.start()],False,False,None))
        tok=m.group(0)
        if tok.startswith('**'): out.append((tok[2:-2],True,False,None))
        elif tok.startswith('`'): out.append((tok[1:-1],False,True,None))
        else:
            lm=re.match(r'\[(.+?)\]\((.+?)\)',tok); out.append((lm.group(1),False,False,lm.group(2)))
        pos=m.end()
    if pos<len(text): out.append((text[pos:],False,False,None))
    return out
def ih(text):
    parts=[]
    for t,b,c,href in tokenize(text):
        e=htmllib.escape(t)
        if c: e=f'<code>{e}</code>'
        if b: e=f'<strong>{e}</strong>'
        if href: e=f'<a href="{htmllib.escape(href)}">{e}</a>'
        parts.append(e)
    return ''.join(parts)
css="""@page{size:A4;margin:17mm 15mm;}*{box-sizing:border-box;}
body{font-family:"Segoe UI",Arial,sans-serif;color:#1f2933;line-height:1.5;font-size:10.5pt;}
h1{color:#0b5394;font-size:20pt;border-bottom:3px solid #0b5394;padding-bottom:8px;}
h2{color:#0b5394;font-size:14.5pt;margin-top:22px;border-bottom:1px solid #cbd5e1;padding-bottom:3px;page-break-after:avoid;}
h3{color:#134f5c;font-size:12pt;margin-top:16px;page-break-after:avoid;}
blockquote{background:#f0f6fb;border-left:4px solid #0b5394;margin:10px 0;padding:7px 13px;color:#334155;}
table{border-collapse:collapse;width:100%;margin:11px 0;font-size:9pt;page-break-inside:avoid;}
th{background:#0b5394;color:#fff;text-align:left;padding:6px 7px;}
td{border:1px solid #d1d9e0;padding:5px 7px;vertical-align:top;}
tr:nth-child(even) td{background:#f6f9fc;}
a{color:#0b5394;text-decoration:none;word-break:break-all;}
code{background:#eef2f6;padding:1px 4px;border-radius:3px;font-family:Consolas,monospace;font-size:9pt;}
ul,ol{margin:6px 0;padding-left:22px;}li{margin:2px 0;}
hr{border:none;border-top:1px solid #e2e8f0;margin:18px 0;}"""
with open(SRC,encoding='utf-8') as f: blocks=parse_blocks(f.readlines())
out=['<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">',f'<style>{css}</style></head><body>']
for kind,p in blocks:
    if kind in('h1','h2','h3'): out.append(f'<{kind}>{ih(p)}</{kind}>')
    elif kind=='p': out.append(f'<p>{ih(p)}</p>')
    elif kind=='hr': out.append('<hr>')
    elif kind=='quote': out.append(f'<blockquote>{ih(p)}</blockquote>')
    elif kind=='code': out.append(f'<pre>{htmllib.escape(p)}</pre>')
    elif kind=='ul': out.append('<ul>'+''.join(f'<li>{ih(it)}</li>' for it in p)+'</ul>')
    elif kind=='ol': out.append('<ol>'+''.join(f'<li>{ih(it)}</li>' for it in p)+'</ol>')
    elif kind=='table':
        header,rows=p
        h='<tr>'+''.join(f'<th>{ih(c)}</th>' for c in header)+'</tr>'
        r=''.join('<tr>'+''.join(f'<td>{ih(c)}</td>' for c in row)+'</tr>' for row in rows)
        out.append(f'<table>{h}{r}</table>')
out.append('</body></html>')
with open(HTML_OUT,'w',encoding='utf-8') as f: f.write('\n'.join(out))
print("HTML OK")
