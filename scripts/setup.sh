#!/usr/bin/env bash
set -euo pipefail

# 一键搭建 VLESS + Reality 节点（3x-ui 面板），可选套住宅 IP
# 用法：bash <(curl -fsSL https://raw.githubusercontent.com/Finderlzy/Writing/main/scripts/setup.sh)
PORT=8555
PANEL_PORT=8080

if [ "$(id -u)" -ne 0 ]; then echo "请用 root 用户运行"; exit 1; fi
if [ -e /etc/x-ui ]; then echo "这台服务器装过 3x-ui，请换一台全新的 VPS"; exit 1; fi

DETECTED=$(curl -s4 -m 10 https://api.ipify.org || true)
read -rp "服务器 IP 是 ${DETECTED:-（没检测到）} 吗？对就直接回车，不对就输入你 SSH 连接用的 IP: " IP
IP=${IP:-$DETECTED}
read -rp "住宅代理 IP（方案二直接回车跳过）: " RES_IP
if [ -n "$RES_IP" ]; then
  read -rp "住宅代理端口: " RES_PORT
  read -rp "住宅代理用户名: " RES_USER
  read -rp "住宅代理密码: " RES_PASS
fi
if [ -z "$IP" ]; then echo "服务器 IP 不能为空"; exit 1; fi

apt update
apt install -y curl openssl ufw python3

# ---- 先测住宅代理，不通就不往下装 ----
if [ -n "$RES_IP" ]; then
  echo "== 测试住宅代理 =="
  RES_OUT=$(curl -s -m 15 --socks5-hostname "$RES_IP:$RES_PORT" --proxy-user "$RES_USER:$RES_PASS" https://ipinfo.io/ip || true)
  if [ -z "$RES_OUT" ]; then
    echo "住宅代理连不上。去商家后台检查：端口、用户名密码、IP 白名单（把 $IP 加进去）、套餐是否生效。"
    exit 1
  fi
  echo "住宅代理可用，出口 IP：$RES_OUT"
fi

# ---- 安装 3x-ui（面板只监听本机，用 SSH 隧道访问）----
XUI_NONINTERACTIVE=1 XUI_PANEL_PORT=$PANEL_PORT XUI_SSL_MODE=none XUI_SERVER_IP=$IP XUI_ENABLE_FAIL2BAN=false \
  bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/v3.9.0/install.sh) v3.9.0 </dev/null
/usr/local/x-ui/x-ui setting -listenIP 127.0.0.1 >/dev/null
systemctl restart x-ui
. /etc/x-ui/install-result.env
B="http://127.0.0.1:$PANEL_PORT/$XUI_WEB_BASE_PATH"
for i in $(seq 1 30); do curl -s -o /dev/null "$B/" && break; sleep 1; done

# ---- 在面板里建入站、客户端、住宅出站 ----
export IP PORT B XUI_API_TOKEN RES_IP RES_PORT="${RES_PORT:-}" RES_USER="${RES_USER:-}" RES_PASS="${RES_PASS:-}"
python3 - <<'PY'
import json, os, secrets, urllib.parse, urllib.request

E = os.environ
def api(path, form=None, body=None):
    data, headers = None, {"Authorization": "Bearer " + E["XUI_API_TOKEN"]}
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
    elif body is not None:
        data, headers["Content-Type"] = json.dumps(body).encode(), "application/json"
    req = urllib.request.Request(E["B"] + path, data=data, headers=headers, method="POST" if data is not None or path.endswith("/") else "GET")
    res = json.load(urllib.request.urlopen(req, timeout=120))
    if not res.get("success"):
        raise SystemExit(f"面板接口出错：{path} {res.get('msg')}")
    return res["obj"]

# 伪装目标：和面板里点“扫描”一样，挑第一个可用的
for target in ["www.microsoft.com:443", "www.apple.com:443", "www.amazon.com:443"]:
    scan = api("/panel/api/server/scanRealityTarget", form={"target": target})
    if scan.get("feasible"):
        break
else:
    raise SystemExit("几个伪装网站都不可用，请到面板里手动扫描换一个")
print("伪装网站：" + target)

keys = api("/panel/api/server/getNewX25519Cert")
uuid = api("/panel/api/server/getNewUUID")["uuid"]
port = int(E["PORT"])
settings = {"clients": [{"id": uuid, "flow": "xtls-rprx-vision", "email": "me", "limitIp": 0, "totalGB": 0,
                         "expiryTime": 0, "enable": True, "tgId": "", "subId": secrets.token_hex(8), "reset": 0}],
            "decryption": "none", "fallbacks": []}
stream = {"network": "tcp", "security": "reality",
          "externalProxy": [{"forceTls": "same", "dest": E["IP"], "port": port, "remark": ""}],
          "realitySettings": {"show": False, "xver": 0, "target": target, "serverNames": scan["serverNames"],
                              "privateKey": keys["privateKey"], "minClientVer": "", "maxClientVer": "",
                              "maxTimediff": 0, "shortIds": [secrets.token_hex(4)],
                              "settings": {"publicKey": keys["publicKey"], "fingerprint": "chrome",
                                           "serverName": "", "spiderX": "/"}},
          "tcpSettings": {"acceptProxyProtocol": False, "header": {"type": "none"}}}
sniffing = {"enabled": True, "destOverride": ["http", "tls", "quic"], "metadataOnly": False, "routeOnly": True}
api("/panel/api/inbounds/add", body={"up": 0, "down": 0, "total": 0, "remark": "my-node", "enable": True,
                                     "expiryTime": 0, "listen": "", "port": port, "protocol": "vless",
                                     "settings": json.dumps(settings), "streamSettings": json.dumps(stream),
                                     "sniffing": json.dumps(sniffing)})

if E["RES_IP"]:
    xray = json.loads(api("/panel/api/xray/"))["xraySetting"]
    xray["outbounds"].append({"tag": "residential", "protocol": "socks", "settings": {"servers": [{
        "address": E["RES_IP"], "port": int(E["RES_PORT"]),
        "users": [{"user": E["RES_USER"], "pass": E["RES_PASS"]}]}]}})
    xray["routing"]["rules"].insert(1, {"type": "field", "outboundTag": "residential",
                                        "domain": ["geosite:anthropic", "domain:ipinfo.io"]})
    api("/panel/api/xray/update", form={"xraySetting": json.dumps(xray)})
api("/panel/api/server/restartXrayService", form={})

link = api("/panel/api/inbounds/allLinks")[0]
open("/root/vless.txt", "w").write(link + "\n")
PY

# ---- 防火墙：放行 SSH 和节点端口 ----
SSH_PORT=$(ss -tlnpH | awk '/sshd/ {sub(/.*:/, "", $4); print $4; exit}')
ufw allow "${SSH_PORT:-22}"/tcp
ufw allow "$PORT"/tcp
ufw --force enable

# ---- 自测：服务器自己连自己的节点 ----
sleep 3
export LINK=$(cat /root/vless.txt) XRAY=$(ls /usr/local/x-ui/bin/xray-linux-* | head -1)
python3 - <<'PY'
import json, os, subprocess, time, urllib.parse
u = urllib.parse.urlparse(os.environ["LINK"]); q = dict(urllib.parse.parse_qsl(u.query))
client = {"inbounds": [{"port": 10899, "listen": "127.0.0.1", "protocol": "socks"}],
          "outbounds": [{"protocol": "vless", "settings": {"vnext": [{"address": "127.0.0.1", "port": u.port,
              "users": [{"id": u.username, "encryption": "none", "flow": q.get("flow", "")}]}]},
              "streamSettings": {"network": "tcp", "security": "reality", "realitySettings": {
                  "serverName": q["sni"], "fingerprint": q.get("fp", "chrome"), "publicKey": q["pbk"],
                  "shortId": q.get("sid", ""), "spiderX": q.get("spx", "")}}}]}
json.dump(client, open("/root/selftest.json", "w"))
p = subprocess.Popen([os.environ["XRAY"], "run", "-c", "/root/selftest.json"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
def via_node(url, fmt):
    return subprocess.run(["curl", "-s", "-m", "15", "-x", "socks5h://127.0.0.1:10899", "-o", "/dev/null" if fmt else "-",
                           "-w", fmt, url], capture_output=True, text=True).stdout.strip()
ok = via_node("https://www.google.com/generate_204", "%{http_code}") == "204"
print("== 节点自测：" + ("成功" if ok else "失败") + " ==")
if ok and os.environ.get("RES_IP"):
    print("== 走节点访问 ipinfo.io 的出口 IP：" + (via_node("https://ipinfo.io/ip", "") or "取不到") + " ==")
p.terminate(); os.remove("/root/selftest.json")
PY

echo
echo "===== 完成 ====="
echo "节点链接（复制下面这行导入代理软件，也存在 /root/vless.txt）："
cat /root/vless.txt
echo
echo "面板（排查用，只能通过 SSH 隧道打开）："
echo "  1. 在自己电脑上运行：ssh -L $PANEL_PORT:127.0.0.1:$PANEL_PORT root@$IP"
echo "  2. 浏览器打开：http://127.0.0.1:$PANEL_PORT/$XUI_WEB_BASE_PATH"
echo "  3. 用户名：$XUI_USERNAME  密码：$XUI_PASSWORD"
echo "  忘了的话运行：cat /etc/x-ui/install-result.env"
