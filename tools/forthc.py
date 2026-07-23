#!/usr/bin/env python3
"""Compile a small Forth subset to a freestanding i386 ELF32."""
import argparse,re,subprocess,tempfile
from pathlib import Path
OPS={'+':"binop('+');",'-':"binop('-');",'*':"binop('*');",'/':"binop('/');",'MOD':"binop('%');",'DUP':'dup_();','DROP':'pop();','SWAP':'swap_();','OVER':'over_();','.':'dot();','EMIT':'emit_();','CR':"putc_('\\n');"}
RT=r'''typedef unsigned char u8;typedef int i32;static volatile u8*out=(volatile u8*)0x00500000;static i32 s[64];static int n=0,e=0;static void putc_(int c){unsigned p=out[0];if(p<250){out[1+p]=c;out[0]=p+1;}}static void puts_(const char*x){while(*x)putc_(*x++);}static void push(i32 v){if(n<64)s[n++]=v;else{e=1;puts_("OVERFLOW\n");}}static i32 pop(void){if(n)return s[--n];e=1;puts_("UNDERFLOW\n");return 0;}static void binop(int o){i32 b=pop(),a=pop();if(e)return;if((o=='/'||o=='%')&&!b){e=1;puts_("DIV0\n");return;}push(o=='+'?a+b:o=='-'?a-b:o=='*'?a*b:o=='/'?a/b:a%b);}static void dup_(void){if(n)push(s[n-1]);else pop();}static void swap_(void){i32 b=pop(),a=pop();if(!e){push(b);push(a);}}static void over_(void){if(n>1)push(s[n-2]);else pop();}static void num(i32 v){char b[12];int k=0;if(!v){putc_('0');return;}if(v<0){putc_('-');v=-v;}while(v){b[k++]='0'+v%10;v/=10;}while(k)putc_(b[--k]);}static void dot(void){i32 v=pop();if(!e){num(v);putc_(' ');}}static void emit_(void){i32 v=pop();if(!e)putc_(v);}int _start(void){out[0]=0;BODY return e?1:0;}'''
def body(text):
 r=[]
 for raw in text.split():
  t=raw.upper()
  if re.fullmatch(r'-?\d+',t): r.append(f'push({int(t)});')
  elif t in OPS:r.append(OPS[t])
  else:raise SystemExit(f'unsupported word: {raw}')
 return ''.join(r)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as d:
  c=Path(d)/'p.c';c.write_text(RT.replace('BODY',body(a.source.read_text())),encoding='utf-8')
  subprocess.run(['gcc','-m32','-ffreestanding','-fno-pic','-fno-pie','-fno-stack-protector','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-T,extension/hello.ld','-o',str(a.output),str(c)],check=True)
 print(f'compiled {a.source} -> {a.output}')
if __name__=='__main__':main()