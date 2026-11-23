#!/bin/bash
# baixa devagar (o Commons limita a taxa) os arquivos que deram 429
cd "$(dirname "$0")/reais"
for rodada in 1 2 3 4 5; do
  falta=0
  for p in "blandy_antes|Mary (Molly) Blandy before her execution, 1752 Wellcome L0036006.jpg" "dybbuk_1922|Dybbuk1922.jpg" "dybbuk_22|Dybbuk22.png"; do
    k=${p%%|*}; t=${p#*|}
    if [ -s $k.jpg ] && file $k.jpg | grep -qE "JPEG|PNG"; then continue; fi
    u="https://commons.wikimedia.org/wiki/Special:FilePath/$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$t")?width=2000"
    code=$(curl -sL -A "VideoResearchTool/1.0 (image search for a video project)" -o $k.jpg -w "%{http_code}" "$u")
    echo "$rodada $k $code"; [ "$code" = 200 ] || { rm -f $k.jpg; falta=1; }
    sleep 45
  done
  [ $falta = 0 ] && break
  sleep 180
done
echo FIM
