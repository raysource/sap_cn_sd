#!/usr/bin/env bash
# 验证快照：gzip 完整性 / 条目数 / sap_cn 计数 / 归档内 SVG 与磁盘一致
set -euo pipefail
cd /Users/jason/Desktop/work/training
A="_snapshots/sap_training_sites_9sites_20260913_221624_cn.tar.gz"
gzip -t "$A" && echo "gzip OK"
echo "entries: $(tar -tzf "$A" | wc -l | tr -d ' ')"
echo "sap_cn entries: $(tar -tzf "$A" | grep -c '^sap_cn/')"
for f in sap_cn/index.html sap_cn/org.html sap_cn/delivery.html sap_cn/SAPSD_课程大纲_学习WBS.xlsx sap_cn/README.md sap_cn/work/gui_screenshot_text.json; do
  if tar -tzf "$A" | grep -q "^${f}$"; then echo "OK   $f"; else echo "MISS $f"; fi
done
# 归档内的自绘图 must match disk (md5)
tmp="$(mktemp -d)"
tar -xzf "$A" -C "$tmp" sap_cn/assets/diagrams
for s in "$tmp"/sap_cn/assets/diagrams/*.svg; do
  b="$(md5 -q "$s")"; d="$(md5 -q "sap_cn/assets/diagrams/$(basename "$s")")"
  if [ "$b" = "$d" ]; then echo "same  $(basename "$s")  $b"; else echo "DIFF  $(basename "$s")  archive=$b disk=$d"; fi
done
rm -rf "$tmp"
ls -lh "$A"
