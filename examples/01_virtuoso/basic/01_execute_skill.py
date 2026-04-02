#!/usr/bin/env python3
"""Hello World — execute SKILL expressions and display return values locally.

Prerequisites:
- virtuoso-bridge service running (virtuoso-bridge start)
- RAMIC daemon loaded in Virtuoso CIW
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from _timing import format_elapsed, timed_call
from virtuoso_bridge import BridgeClient

client = BridgeClient()

stmts = [
    r'printf("\n\n\n\n\n==============================================\nHello, Virtuoso!\n")',
    r'let((v) v=getCurrentTime()  printf("[Date & Time]     %s\n" v) v)',
    r'let((v) v=getVersion()      printf("[Cadence Version] %s\n" v) v)',
    r'let((v) v=getSkillVersion() printf("[SKILL Version]   %s\n" v) v)',
    r'let((v) v=getWorkingDir()   printf("[Working Dir]     %s\n" v) v)',
    r'let((v) v=getHostName()     printf("[Host Name]       %s\n" v) v)',
    "1 + 2",
    'strcat("Hello" " from SKILL")',
    r'printf("==============================================\n")',
]
for stmt in stmts:
    elapsed, response = timed_call(lambda s=stmt: client.execute_skill(s))
    output = response.get("result", {}).get("output")
    print(f"[OK] {stmt}  =>  {output!r}  [{format_elapsed(elapsed)}]")
